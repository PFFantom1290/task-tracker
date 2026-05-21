"""
Strategy pattern — Behavioral.

Encapsulates interchangeable sorting and filtering algorithms so that
TaskService can swap them at runtime without altering its own code.

Sorting strategies: SortByDueDate, SortByPriority, SortByTitle, SortByCreated
Filtering strategies: FilterByPriority, FilterByStatus, FilterByDateRange,
                      FilterByCategory, CompositeFilter
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.models.task import Priority, Status, Task

# ================================================================== #
#  SORT STRATEGIES                                                     #
# ================================================================== #

class SortStrategy(ABC):
    """Abstract sort strategy."""

    @abstractmethod
    def sort(self, tasks: list[Task], reverse: bool = False) -> list[Task]:
        ...


class SortByDueDate(SortStrategy):
    """Sort tasks by due date; tasks without a due date go to the end."""

    def sort(self, tasks: list[Task], reverse: bool = False) -> list[Task]:
        def key(t: Task):
            return t.due_date or datetime.max
        return sorted(tasks, key=key, reverse=reverse)


class SortByPriority(SortStrategy):
    """Sort tasks by priority (LOW → CRITICAL by default)."""

    _ORDER = {
        Priority.LOW: 0,
        Priority.MEDIUM: 1,
        Priority.HIGH: 2,
        Priority.CRITICAL: 3,
    }

    def sort(self, tasks: list[Task], reverse: bool = False) -> list[Task]:
        return sorted(tasks, key=lambda t: self._ORDER[t.priority], reverse=reverse)


class SortByTitle(SortStrategy):
    """Sort tasks alphabetically by title."""

    def sort(self, tasks: list[Task], reverse: bool = False) -> list[Task]:
        return sorted(tasks, key=lambda t: t.title.lower(), reverse=reverse)


class SortByCreated(SortStrategy):
    """Sort tasks by creation timestamp."""

    def sort(self, tasks: list[Task], reverse: bool = False) -> list[Task]:
        return sorted(tasks, key=lambda t: t.created_at, reverse=reverse)


def get_sort_strategy(field: str) -> SortStrategy:
    strategies: dict[str, SortStrategy] = {
        "due_date": SortByDueDate(),
        "priority": SortByPriority(),
        "title": SortByTitle(),
        "created_at": SortByCreated(),
    }
    if field not in strategies:
        raise ValueError(f"Unknown sort field '{field}'. Choose from: {list(strategies)}")
    return strategies[field]


# ================================================================== #
#  FILTER STRATEGIES                                                   #
# ================================================================== #

class FilterStrategy(ABC):
    """Abstract filter strategy."""

    @abstractmethod
    def apply(self, tasks: list[Task]) -> list[Task]:
        ...


class FilterByPriority(FilterStrategy):
    """Keep only tasks matching the given priority."""

    def __init__(self, priority: str):
        self._priority = Priority(priority)

    def apply(self, tasks: list[Task]) -> list[Task]:
        return [t for t in tasks if t.priority == self._priority]


class FilterByStatus(FilterStrategy):
    """Keep only tasks matching the given status."""

    def __init__(self, status: str):
        self._status = Status(status)

    def apply(self, tasks: list[Task]) -> list[Task]:
        return [t for t in tasks if t.status == self._status]


class FilterByDateRange(FilterStrategy):
    """Keep only tasks whose due date falls within [start, end]."""

    def __init__(self, start: datetime | None = None, end: datetime | None = None):
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


class FilterByCategory(FilterStrategy):
    """Keep only tasks in the given category (case-insensitive)."""

    def __init__(self, category: str):
        self._category = category.lower()

    def apply(self, tasks: list[Task]) -> list[Task]:
        return [t for t in tasks if t.category.lower() == self._category]


class FilterOverdue(FilterStrategy):
    """Keep only overdue tasks."""

    def apply(self, tasks: list[Task]) -> list[Task]:
        return [t for t in tasks if t.is_overdue()]


class CompositeFilter(FilterStrategy):
    """Combines multiple filters with AND semantics (all must pass)."""

    def __init__(self, *filters: FilterStrategy):
        self._filters = list(filters)

    def add(self, f: FilterStrategy) -> CompositeFilter:
        self._filters.append(f)
        return self

    def apply(self, tasks: list[Task]) -> list[Task]:
        result = tasks
        for f in self._filters:
            result = f.apply(result)
        return result
