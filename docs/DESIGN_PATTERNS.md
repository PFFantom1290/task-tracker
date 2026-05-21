# DESIGN_PATTERNS.md — Design Patterns Documentation

## Pattern 1 — Factory Method (Creational)

### Which pattern and category
**Factory Method** — Creational category.

### Problem it solves
The CLI accepts a `--type` argument that determines what kind of task to create
(`standard`, `recurring`, `subtask`). Without the pattern, `TaskService.create()`
would contain a growing `if/elif` chain that couples the service to every task
variant. Adding a new type (e.g. `milestone`) would require modifying the service.

The Factory Method pattern decouples **who creates** a task from **how it is created**:
the service simply calls `factory.create(...)` — the concrete factory decides
the variant's construction logic.

### Participants
| Class | Role |
|-------|------|
| `TaskFactory` | Abstract Creator — declares `create()` |
| `StandardTaskFactory` | Concrete Creator — plain one-off task |
| `RecurringTaskFactory` | Concrete Creator — adds `recurring` tag, auto-assigns due date |
| `SubTaskFactory` | Concrete Creator — adds `parent:<id>` tag |
| `get_factory(type)` | Registry — maps type string → concrete factory |

### UML Class Diagram

```
┌─────────────────────┐
│    <<abstract>>     │
│    TaskFactory      │
├─────────────────────┤
│ + create(...): Task │◄──────────────────────────────┐
│ + create_and_       │                               │
│   validate(): Task  │                               │
└─────────────────────┘                               │
         ▲                                            │
         │ inherits                                   │
    ┌────┴──────────────┬──────────────────────┐      │
    │                  │                      │      │
┌───┴────────────┐ ┌───┴──────────────┐ ┌────┴────────┤
│StandardTask    │ │RecurringTask     │ │SubTask      │
│Factory         │ │Factory           │ │Factory      │
├────────────────┤ ├──────────────────┤ ├─────────────┤
│ create(): Task │ │interval_days: int│ │parent_id:str│
└────────────────┘ │ create(): Task   │ │create():Task│
                   └──────────────────┘ └─────────────┘
                                                      │
                                              creates │
                                                      ▼
                                               ┌──────────┐
                                               │   Task   │
                                               └──────────┘
```

### Files implementing this pattern
- `src/patterns/factory.py` — all factory classes
- `src/services/task_service.py` — uses `self._factory.create(...)`
- `src/cli/commands.py` — calls `get_factory(args.task_type)`

### Real benefit
Adding a new task type (e.g. `MilestoneTaskFactory`) requires **zero changes**
to `TaskService` or the CLI dispatcher — only a new class in `factory.py` and
one line in `get_factory()`.

---

## Pattern 2 — Strategy (Behavioral)

### Which pattern and category
**Strategy** — Behavioral category.

### Problem it solves
The `list` command supports multiple sort orders (`due_date`, `priority`,
`title`, `created_at`) and multiple independent filter criteria (by priority,
by status, by date range, by category). Without Strategy, `TaskService.list_all()`
would need deeply nested conditionals for every combination.

Strategy encapsulates each algorithm as its own object. The service calls
`strategy.sort(tasks)` or `filter.apply(tasks)` without knowing the implementation.
Filters can also be composed via `CompositeFilter` for AND-semantics at runtime.

### Participants

**Sort strategies:**
| Class | Algorithm |
|-------|-----------|
| `SortByDueDate` | Sort by `due_date`; `None` → end |
| `SortByPriority` | Sort LOW→CRITICAL |
| `SortByTitle` | Alphabetical |
| `SortByCreated` | Chronological |

**Filter strategies:**
| Class | Criterion |
|-------|-----------|
| `FilterByPriority` | Exact priority match |
| `FilterByStatus` | Exact status match |
| `FilterByDateRange` | Due date in [start, end] |
| `FilterByCategory` | Case-insensitive category match |
| `FilterOverdue` | `is_overdue() == True` |
| `CompositeFilter` | AND-combination of multiple filters |

### UML Class Diagram

```
┌──────────────────────┐         ┌──────────────────────┐
│   <<abstract>>       │         │   <<abstract>>       │
│   SortStrategy       │         │   FilterStrategy     │
├──────────────────────┤         ├──────────────────────┤
│ sort(tasks,rev):list │         │ apply(tasks): list   │
└──────────────────────┘         └──────────────────────┘
         ▲                                ▲
    ┌────┴────────────────┐          ┌────┴────────────────────────┐
    │         │           │          │      │          │            │
┌───┴──┐ ┌───┴──┐ ┌───┴──┐    ┌────┴──┐ ┌─┴────┐ ┌──┴──────┐ ┌──┴──────┐
│ByDue │ │ByPri │ │ByTitl│    │ByPrio │ │ByStat│ │ByDateRng│ │Composite│
│Date  │ │ority │ │e     │    │ity    │ │us    │ │         │ │Filter   │
└──────┘ └──────┘ └──────┘    └───────┘ └──────┘ └─────────┘ └─────────┘

TaskService uses both strategies:
  list_all(sort_strategy=..., filters=[...])
```

### Files implementing this pattern
- `src/patterns/strategy.py` — all strategy classes
- `src/services/task_service.py` — `list_all()` accepts strategies as parameters
- `src/cli/commands.py` — builds strategies from CLI arguments

### Real benefit
The `CompositeFilter` means a user can apply `--priority high --status todo --overdue`
simultaneously with no changes to any existing class — new filter criteria
require only one new class implementing `FilterStrategy.apply()`.

---

## Pattern 3 — Observer (Behavioral)

### Which pattern and category
**Observer** — Behavioral category.

### Problem it solves
When tasks are created, updated, deleted, or found to be overdue, other
components need to react (log the event, show a warning). Without Observer,
`TaskService` would directly call specific notification functions, coupling
it to every consumer. Adding a new reaction (e.g. email notification) would
require modifying the service.

Observer decouples the subject (`TaskEventBus`) from its listeners.

### Participants
| Class | Role |
|-------|------|
| `TaskObserver` | Abstract observer |
| `OverdueNotifier` | Concrete observer — prints warnings for overdue tasks |
| `AuditLogger` | Concrete observer — records every event in an in-memory log |
| `TaskEventBus` | Subject — maintains observer list, dispatches events |

### UML Class Diagram

```
┌─────────────────────┐      emits      ┌─────────────────────┐
│   TaskEventBus      │────────────────►│  <<abstract>>       │
├─────────────────────┤                 │  TaskObserver       │
│ subscribe(obs)      │                 ├─────────────────────┤
│ unsubscribe(obs)    │                 │ on_event(ev, task)  │
│ emit(event, task)   │                 └─────────────────────┘
└─────────────────────┘                          ▲
         ▲                                  ┌────┴──────────────┐
         │ used by                          │                   │
  TaskService                     ┌─────────┴────┐   ┌─────────┴────┐
                                  │OverdueNotif  │   │ AuditLogger  │
                                  │-er           │   │              │
                                  ├──────────────┤   ├──────────────┤
                                  │notifications │   │ log: list    │
                                  └──────────────┘   └──────────────┘
```

### Files implementing this pattern
- `src/patterns/observer.py` — event bus + all observers
- `src/services/task_service.py` — calls `self._event_bus.emit(...)`
- `src/cli/commands.py` — wires up observers at startup

### Real benefit
A future email-notification observer can be added by creating one new class
that implements `on_event()` and calling `event_bus.subscribe(EmailNotifier())`.
The service is not touched at all.
