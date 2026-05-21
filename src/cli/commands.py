"""
CLI layer — parses arguments and delegates to TaskService / ExportService.

Commands:
  add       Create a new task
  list      List tasks with optional sort/filter
  show      Show a single task in detail
  update    Update task fields
  delete    Delete a task
  search    Full-text keyword search
  export    Export tasks to JSON or CSV
  stats     Display statistics summary
  undo      Undo last mutating operation
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from src.models.task import Priority, Status
from src.patterns.command import CommandHistory, DeleteCommand, UpdateCommand
from src.patterns.factory import get_factory
from src.patterns.observer import AuditLogger, OverdueNotifier, TaskEventBus
from src.patterns.strategy import (
    FilterByCategory,
    FilterByDateRange,
    FilterByPriority,
    FilterByStatus,
    FilterOverdue,
    get_sort_strategy,
)
from src.services.export_service import ExportService
from src.services.task_service import TaskNotFoundError, TaskService

# ------------------------------------------------------------------ #
#  Formatting helpers                                                  #
# ------------------------------------------------------------------ #

PRIORITY_COLOR = {
    "low": "\033[32m",
    "medium": "\033[33m",
    "high": "\033[31m",
    "critical": "\033[35m",
}
RESET = "\033[0m"
BOLD = "\033[1m"


def _fmt_priority(p: str) -> str:
    color = PRIORITY_COLOR.get(p, "")
    return f"{color}{p.upper()}{RESET}"


def _fmt_date(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d") if dt else "—"


def _print_task_row(task, overdue_ids: set = None) -> None:
    overdue_ids = overdue_ids or set()
    overdue_flag = " ⚠ OVERDUE" if task.id in overdue_ids else ""
    due = _fmt_date(task.due_date)
    print(
        f"  {BOLD}{task.id}{RESET}  "
        f"{task.title[:40]:<40}  "
        f"{_fmt_priority(task.priority.value):<18}  "
        f"{task.status.value:<12}  "
        f"{task.category:<15}  "
        f"due:{due}{overdue_flag}"
    )


def _print_task_detail(task) -> None:
    overdue = " ⚠ OVERDUE" if task.is_overdue() else ""
    print(f"\n{'─'*60}")
    print(f"  {BOLD}ID      {RESET}: {task.id}")
    print(f"  {BOLD}Title   {RESET}: {task.title}")
    print(f"  {BOLD}Desc    {RESET}: {task.description or '(none)'}")
    print(f"  {BOLD}Priority{RESET}: {_fmt_priority(task.priority.value)}")
    print(f"  {BOLD}Status  {RESET}: {task.status.value}")
    print(f"  {BOLD}Category{RESET}: {task.category}")
    print(f"  {BOLD}Due date{RESET}: {_fmt_date(task.due_date)}{overdue}")
    print(f"  {BOLD}Created {RESET}: {task.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"  {BOLD}Tags    {RESET}: {', '.join(task.tags) or '(none)'}")
    print(f"{'─'*60}\n")


def _parse_date(value: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Invalid date '{value}'. Use YYYY-MM-DD.")


# ------------------------------------------------------------------ #
#  Argument parser                                                     #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tasks",
        description="Personal Task Tracker — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── add ────────────────────────────────────────────────────────── #
    p_add = sub.add_parser("add", help="Create a new task")
    p_add.add_argument("title", help="Task title")
    p_add.add_argument("-d", "--description", default="", help="Longer description")
    p_add.add_argument(
        "-p", "--priority",
        choices=Priority.values(), default="medium",
        help="Priority level (default: medium)",
    )
    p_add.add_argument("-c", "--category", default="general", help="Category label")
    p_add.add_argument("--due", type=_parse_date, metavar="YYYY-MM-DD", help="Due date")
    p_add.add_argument("--tags", nargs="*", default=[], help="Space-separated tags")
    p_add.add_argument(
        "--type", dest="task_type",
        choices=["standard", "recurring", "subtask"], default="standard",
        help="Task variant (default: standard)",
    )
    p_add.add_argument("--parent", dest="parent_id", default="", help="Parent task ID (for subtasks)")
    p_add.add_argument("--interval", type=int, default=7, help="Recurrence interval in days")

    # ── list ───────────────────────────────────────────────────────── #
    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--sort", choices=["due_date", "priority", "title", "created_at"],
                        default="created_at", help="Sort field")
    p_list.add_argument("--desc", action="store_true", help="Descending order")
    p_list.add_argument("--priority", choices=Priority.values(), help="Filter by priority")
    p_list.add_argument("--status", choices=Status.values(), help="Filter by status")
    p_list.add_argument("--category", help="Filter by category")
    p_list.add_argument("--from", dest="from_date", type=_parse_date, metavar="YYYY-MM-DD")
    p_list.add_argument("--to", dest="to_date", type=_parse_date, metavar="YYYY-MM-DD")
    p_list.add_argument("--overdue", action="store_true", help="Show only overdue tasks")

    # ── show ───────────────────────────────────────────────────────── #
    p_show = sub.add_parser("show", help="Show task details")
    p_show.add_argument("id", help="Task ID")

    # ── update ─────────────────────────────────────────────────────── #
    p_update = sub.add_parser("update", help="Update a task")
    p_update.add_argument("id", help="Task ID")
    p_update.add_argument("--title", help="New title")
    p_update.add_argument("--description", help="New description")
    p_update.add_argument("--priority", choices=Priority.values())
    p_update.add_argument("--status", choices=Status.values())
    p_update.add_argument("--category")
    p_update.add_argument("--due", type=_parse_date, dest="due_date", metavar="YYYY-MM-DD")
    p_update.add_argument("--tags", nargs="*")

    # ── delete ─────────────────────────────────────────────────────── #
    p_del = sub.add_parser("delete", help="Delete a task")
    p_del.add_argument("id", help="Task ID")
    p_del.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # ── search ─────────────────────────────────────────────────────── #
    p_search = sub.add_parser("search", help="Search tasks by keyword")
    p_search.add_argument("keyword", help="Keyword to search for")

    # ── export ─────────────────────────────────────────────────────── #
    p_export = sub.add_parser("export", help="Export tasks")
    p_export.add_argument("--format", choices=["json", "csv"], default="json", dest="fmt")
    p_export.add_argument("--output", default="", help="Output file path")
    p_export.add_argument("--status", choices=Status.values(), help="Filter by status before export")

    # ── stats ──────────────────────────────────────────────────────── #
    sub.add_parser("stats", help="Show statistics")

    # ── undo ───────────────────────────────────────────────────────── #
    sub.add_parser("undo", help="Undo the last delete or update")

    return parser


# ------------------------------------------------------------------ #
#  Command handlers                                                    #
# ------------------------------------------------------------------ #

def cmd_add(args, service: TaskService) -> None:
    factory = get_factory(
        args.task_type,
        interval_days=args.interval,
        parent_id=args.parent_id,
    )
    service.set_factory(factory)
    task = service.create(
        title=args.title,
        description=args.description,
        priority=args.priority,
        category=args.category,
        due_date=args.due,
        tags=args.tags,
    )
    print(f"✓ Created task [{task.id}]: {task.title}")


def cmd_list(args, service: TaskService) -> None:
    sort_strat = get_sort_strategy(args.sort)
    filters = []
    if args.priority:
        filters.append(FilterByPriority(args.priority))
    if args.status:
        filters.append(FilterByStatus(args.status))
    if args.category:
        filters.append(FilterByCategory(args.category))
    if args.from_date or args.to_date:
        filters.append(FilterByDateRange(args.from_date, args.to_date))
    if args.overdue:
        filters.append(FilterOverdue())

    tasks = service.list_all(sort_strategy=sort_strat, reverse=args.desc, filters=filters)
    overdue_ids = {t.id for t in tasks if t.is_overdue()}

    if not tasks:
        print("  (no tasks match the criteria)")
        return

    print(f"\n  {'ID':<8}  {'TITLE':<40}  {'PRIORITY':<10}  {'STATUS':<12}  {'CATEGORY':<15}  DUE")
    print(f"  {'─'*8}  {'─'*40}  {'─'*10}  {'─'*12}  {'─'*15}  {'─'*12}")
    for t in tasks:
        _print_task_row(t, overdue_ids)
    print(f"\n  {len(tasks)} task(s) listed.\n")


def cmd_show(args, service: TaskService) -> None:
    try:
        task = service.get_by_id(args.id)
        _print_task_detail(task)
    except TaskNotFoundError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args, service: TaskService, history: CommandHistory) -> None:
    updates = {}
    for field in ("title", "description", "priority", "status", "category", "due_date", "tags"):
        val = getattr(args, field, None)
        if val is not None:
            updates[field] = val
    if not updates:
        print("✗ No fields specified to update.", file=sys.stderr)
        sys.exit(1)
    try:
        cmd = UpdateCommand(service, args.id, updates)
        history.execute(cmd)
        print(f"✓ Updated task [{args.id}].")
    except TaskNotFoundError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args, service: TaskService, history: CommandHistory) -> None:
    try:
        task = service.get_by_id(args.id)
        if not args.yes:
            confirm = input(f"Delete '{task.title}' [{task.id}]? (y/N): ")
            if confirm.lower() != "y":
                print("Aborted.")
                return
        cmd = DeleteCommand(service, args.id)
        history.execute(cmd)
        print(f"✓ Deleted task [{args.id}].")
    except TaskNotFoundError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args, service: TaskService) -> None:
    results = service.search(args.keyword)
    if not results:
        print(f"  No tasks found matching '{args.keyword}'.")
        return
    print(f"\n  Results for '{args.keyword}':")
    overdue_ids = {t.id for t in results if t.is_overdue()}
    for t in results:
        _print_task_row(t, overdue_ids)
    print(f"\n  {len(results)} result(s).\n")


def cmd_export(args, service: TaskService) -> None:
    tasks = service.list_all()
    if args.status:
        from src.patterns.strategy import FilterByStatus
        tasks = FilterByStatus(args.status).apply(tasks)
    output = args.output or f"tasks_export.{args.fmt}"
    path = ExportService.export(tasks, args.fmt, output)
    print(f"✓ Exported {len(tasks)} task(s) → {path}")


def cmd_stats(args, service: TaskService) -> None:
    s = service.statistics()
    print(f"\n  {'─'*40}")
    print(f"  {BOLD}Task Statistics{RESET}")
    print(f"  {'─'*40}")
    print(f"  Total tasks      : {s['total']}")
    print(f"  Overdue          : {s['overdue']}")
    print(f"  Completion rate  : {s['completion_rate_pct']}%")
    print("\n  By status:")
    for k, v in s["by_status"].items():
        print(f"    {k:<15}: {v}")
    print("\n  By priority:")
    for k, v in s["by_priority"].items():
        print(f"    {k:<15}: {v}")
    print("\n  By category:")
    for k, v in s["by_category"].items():
        print(f"    {k:<15}: {v}")
    print(f"  {'─'*40}\n")


def cmd_undo(args, history: CommandHistory) -> None:
    if history.undo():
        print("✓ Last operation undone.")
    else:
        print("✗ Nothing to undo.")


# ------------------------------------------------------------------ #
#  Main entry point                                                    #
# ------------------------------------------------------------------ #

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Wire up dependencies
    event_bus = TaskEventBus()
    event_bus.subscribe(OverdueNotifier())
    event_bus.subscribe(AuditLogger())

    service = TaskService(event_bus=event_bus)
    history = CommandHistory()

    dispatch = {
        "add": lambda: cmd_add(args, service),
        "list": lambda: cmd_list(args, service),
        "show": lambda: cmd_show(args, service),
        "update": lambda: cmd_update(args, service, history),
        "delete": lambda: cmd_delete(args, service, history),
        "search": lambda: cmd_search(args, service),
        "export": lambda: cmd_export(args, service),
        "stats": lambda: cmd_stats(args, service),
        "undo": lambda: cmd_undo(args, history),
    }

    try:
        dispatch[args.command]()
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as exc:
        print(f"✗ Unexpected error: {exc}", file=sys.stderr)
        return 2
