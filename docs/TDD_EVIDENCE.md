# TDD_EVIDENCE.md — Test-Driven Development Evidence

## Overview

The `FilterByDateRange` strategy was developed using strict TDD:
**Red → Green → Refactor**.

The three-stage commit sequence below demonstrates the cycle.

---

## Feature: Filter tasks by date range

### Stage 1 — RED (failing test written first)

**Commit message:** `test: red — FilterByDateRange filters by date window`

```python
# tests/test_export.py  (written BEFORE any implementation)

def test_wb24_filter_date_range_excludes_outside(self):
    """WB-24: FilterByDateRange excludes tasks outside the window."""
    tasks = [
        make_task("past", due_days=-10),
        make_task("in_range", due_days=5),
        make_task("future", due_days=20),
    ]
    start = datetime.now()
    end = datetime.now() + timedelta(days=10)
    result = FilterByDateRange(start, end).apply(tasks)
    assert len(result) == 1
    assert result[0].title == "in_range"
```

Running `pytest` at this point produced:

```
ImportError: cannot import name 'FilterByDateRange' from 'src.patterns.strategy'
FAILED tests/test_export.py::TestStrategies::test_wb24_filter_date_range_excludes_outside
```

---

### Stage 2 — GREEN (minimal implementation to pass)

**Commit message:** `feat: green — implement FilterByDateRange`

```python
# src/patterns/strategy.py  (minimal passing implementation)

class FilterByDateRange(FilterStrategy):
    def __init__(self, start=None, end=None):
        self._start = start
        self._end = end

    def apply(self, tasks):
        result = []
        for t in tasks:
            if t.due_date is None:
                continue
            if self._start and t.due_date < self._start:
                continue
            if self._end and t.due_date > self._end:
                continue
            result.append(t)
        return result
```

Running `pytest` produced:

```
PASSED tests/test_export.py::TestStrategies::test_wb24_filter_date_range_excludes_outside
```

---

### Stage 3 — REFACTOR (cleaned up, type annotations, docstring added)

**Commit message:** `refactor: add type hints and docstring to FilterByDateRange`

```python
class FilterByDateRange(FilterStrategy):
    """Keep only tasks whose due date falls within [start, end]."""

    def __init__(self, start: Optional[datetime] = None, end: Optional[datetime] = None):
        self._start = start
        self._end = end

    def apply(self, tasks: list[Task]) -> list[Task]:
        result = []
        for t in tasks:
            if t.due_date is None:
                continue
            if self._start and t.due_date < self._start:
                continue
            if self._end and t.due_date > self._end:
                continue
            result.append(t)
        return result
```

All tests still passed after the refactor. No behaviour was changed.

---

## BDD / Acceptance Tests (Given-When-Then)

The following acceptance criteria were written before implementation
and are located in `tests/test_acceptance.py`:

### Scenario AT-01: Create and List
```
Given: an empty task list
When:  the user creates a HIGH-priority task
Then:  the task appears in list_all() with the correct priority
```

### Scenario AT-04: Keyword Search
```
Given: multiple tasks with different content
When:  user searches for "invoice"
Then:  only the task containing "invoice" is returned
```

### Scenario AT-06: Update Persists Across Sessions
```
Given: a task stored on disk
When:  user updates its title and a new service instance is loaded
Then:  the new title is visible in the fresh instance
```

---

## Summary

| Stage | Commit Message | Test Result |
|-------|---------------|-------------|
| Red | `test: red — FilterByDateRange filters by date window` | ❌ FAILED |
| Green | `feat: green — implement FilterByDateRange` | ✅ PASSED |
| Refactor | `refactor: add type hints and docstring to FilterByDateRange` | ✅ PASSED |
