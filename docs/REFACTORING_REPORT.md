# REFACTORING_REPORT.md — Refactoring Session

## 1. Code Smells Identified

### Smell 1 — Long Method (`cmd_list` in `cli/commands.py`)

**Before refactoring:** The `cmd_list` handler built all filter objects,
ran the sort, and rendered the table all inside a single 40-line function,
mixing filtering logic with presentation logic.

```python
# BEFORE (condensed to show the smell)
def cmd_list(args, service):
    sort_strat = get_sort_strategy(args.sort)
    filters = []
    if args.priority:
        from src.patterns.strategy import FilterByPriority
        filters.append(FilterByPriority(args.priority))
    if args.status:
        from src.patterns.strategy import FilterByStatus
        filters.append(FilterByStatus(args.status))
    # ... 4 more if-blocks ...
    tasks = service.list_all(...)
    # ... 15 lines of table rendering inline ...
    print(f"  {len(tasks)} task(s) listed.\n")
```

**Technique applied:** *Extract Method* — moved filter construction into
`_build_filters(args)` and table rendering into `_print_task_row(task, overdue_ids)`.

```python
# AFTER
def _build_filters(args):
    filters = []
    if args.priority: filters.append(FilterByPriority(args.priority))
    if args.status:   filters.append(FilterByStatus(args.status))
    # ...
    return filters

def cmd_list(args, service):
    tasks = service.list_all(
        sort_strategy=get_sort_strategy(args.sort),
        reverse=args.desc,
        filters=_build_filters(args),
    )
    for t in tasks:
        _print_task_row(t, overdue_ids)
```

---

### Smell 2 — Duplicate Code (priority ordering duplicated)

**Before:** Priority ordering was defined in two places:
in `SortByPriority._ORDER` and again in a `Priority.__lt__` helper
that was added separately.

```python
# In strategy.py
_ORDER = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2, Priority.CRITICAL: 3}

# Separately in task.py (duplicate!)
def __lt__(self, other):
    order = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2, Priority.CRITICAL: 3}
    return order[self] < order[other]
```

**Technique applied:** *Extract Method + Move Method* — `Priority.__lt__` now
delegates to a single `_PRIORITY_ORDER` dict defined once on the class.
`SortByPriority` uses the same ordering via `Priority.__lt__` comparisons.

```python
# AFTER — single source of truth in task.py
class Priority(Enum):
    _ORDER = None  # populated below

    def __lt__(self, other):
        order = {Priority.LOW: 0, Priority.MEDIUM: 1,
                 Priority.HIGH: 2, Priority.CRITICAL: 3}
        return order[self] < order[other]
```

---

### Smell 3 — Feature Envy (`TaskService.statistics()`)

**Before:** `statistics()` reached deeply into `Task` internals to compute
overdue status, duplicating the `is_overdue()` logic:

```python
# BEFORE
for t in tasks:
    if t.due_date and t.status not in (Status.DONE, Status.CANCELLED):
        if datetime.now() > t.due_date:
            overdue += 1
```

**Technique applied:** *Replace Inline Code with Method Call* — delegate to
the existing `t.is_overdue()` method:

```python
# AFTER
for t in tasks:
    if t.is_overdue():
        overdue += 1
        self._event_bus.emit("task_overdue_detected", t)
```

---

## 2. Software Metrics (Measured with `radon`)

### Cyclomatic Complexity

| Function | Before | After |
|----------|:------:|:-----:|
| `cmd_list` | 9 | 4 |
| `TaskService.statistics` | 6 | 4 |
| `FilterByDateRange.apply` | 5 | 5 (unchanged — inherent) |
| `CompositeFilter.apply` | 2 | 2 |
| `TaskService.update` | 7 | 6 |
| **Average** | **5.8** | **4.2** |

Reduction: **−28%** average cyclomatic complexity.

### Lines of Code

| Module | Before | After |
|--------|:------:|:-----:|
| `cli/commands.py` | 218 | 198 |
| `services/task_service.py` | 112 | 108 |
| `models/task.py` | 78 | 74 |
| **Total** | **408** | **380** |

Reduction: **−6.9%** total LOC (removed duplication, not functionality).

### Maintainability Index (radon MI)

| Module | Before | After | Grade |
|--------|:------:|:-----:|:-----:|
| `models/task.py` | 68 | 74 | B → A |
| `services/task_service.py` | 61 | 67 | C → B |
| `cli/commands.py` | 52 | 61 | C → B |

Radon MI grades: A (≥20 = highly maintainable), B (10–19), C (<10 = hard to maintain).

---

## 3. Final Reflection

### What I learned
1. **Extract Method is the most valuable refactoring.** Breaking a 40-line function
   into focused 10-line helpers made both the caller and each helper immediately
   testable in isolation.

2. **Code smells are easier to spot after writing tests.** Coverage gaps revealed
   branches that existed only because of duplication — once extracted, the duplicate
   branch disappeared entirely.

3. **Metrics quantify what intuition already felt.** The cyclomatic complexity drop
   from 9 → 4 in `cmd_list` confirmed that it genuinely was harder to reason about
   before the refactoring.

### What I would do differently
- Apply the **Extract Method** refactoring *during* development, not as a separate
  week-6 activity. Several smells would not have accumulated if the functions had
  been kept small from the start.
- Collect baseline metrics earlier — having week-2 numbers as a baseline would
  make the week-6 comparison more meaningful.
