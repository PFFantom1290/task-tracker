"""
TaskService — orchestrates all task operations.

This service layer sits between the CLI and the storage/domain layers.
It delegates to the appropriate patterns:
  - Factory  → task creation
  - Strategy → sorting and filtering
  - Observer → event notifications
  - Command  → undo history
"""

from __future__ import annotations

from datetime import datetime

from src.models.task import Priority, Status, Task
from src.patterns.factory import StandardTaskFactory, TaskFactory
from src.patterns.observer import TaskEventBus
from src.patterns.strategy import (
    FilterStrategy,
    SortByCreated,
    SortStrategy,
)
from src.storage.json_storage import JsonStorage


class TaskNotFoundError(Exception):
    pass


class TaskService:
    """High-level service for managing tasks."""

    def __init__(
        self,
        storage: JsonStorage | None = None,
        factory: TaskFactory | None = None,
        event_bus: TaskEventBus | None = None,
    ):
        self._storage = storage or JsonStorage()
        self._factory = factory or StandardTaskFactory()
        self._event_bus = event_bus or TaskEventBus()
        self._tasks: dict[str, Task] = self._storage.load()

    # ------------------------------------------------------------------ #
    #  Factory setter — allows swapping the factory at runtime            #
    # ------------------------------------------------------------------ #

    def set_factory(self, factory: TaskFactory) -> None:
        self._factory = factory

    # ------------------------------------------------------------------ #
    #  CRUD                                                               #
    # ------------------------------------------------------------------ #

    def create(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        category: str = "general",
        due_date: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        task = self._factory.create(
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
            tags=tags,
        )
        self._tasks[task.id] = task
        self._save()
        self._event_bus.emit("task_created", task)
        return task

    def get_by_id(self, task_id: str) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"No task with id '{task_id}'.")
        return task

    def list_all(
        self,
        sort_strategy: SortStrategy | None = None,
        reverse: bool = False,
        filters: list[FilterStrategy] | None = None,
    ) -> list[Task]:
        tasks = list(self._tasks.values())
        if filters:
            for f in filters:
                tasks = f.apply(tasks)
        strategy = sort_strategy or SortByCreated()
        return strategy.sort(tasks, reverse=reverse)

    def update(self, task_id: str, **kwargs) -> Task:
        task = self.get_by_id(task_id)
        allowed = {"title", "description", "priority", "category", "due_date", "status", "tags"}
        for key, value in kwargs.items():
            if key not in allowed:
                raise ValueError(f"Cannot update field '{key}'.")
            if key == "priority":
                value = Priority(value) if isinstance(value, str) else value
            if key == "status":
                value = Status(value) if isinstance(value, str) else value
            setattr(task, key, value)
        self._save()
        self._event_bus.emit("task_updated", task, fields=list(kwargs.keys()))
        return task

    def delete(self, task_id: str) -> Task:
        task = self.get_by_id(task_id)
        del self._tasks[task_id]
        self._save()
        self._event_bus.emit("task_deleted", task)
        return task

    # ------------------------------------------------------------------ #
    #  Search                                                              #
    # ------------------------------------------------------------------ #

    def search(self, keyword: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.matches_keyword(keyword)]

    # ------------------------------------------------------------------ #
    #  Statistics                                                          #
    # ------------------------------------------------------------------ #

    def statistics(self) -> dict:
        tasks = list(self._tasks.values())
        total = len(tasks)
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        by_category: dict[str, int] = {}
        overdue = 0

        for t in tasks:
            by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
            by_priority[t.priority.value] = by_priority.get(t.priority.value, 0) + 1
            by_category[t.category] = by_category.get(t.category, 0) + 1
            if t.is_overdue():
                overdue += 1
                self._event_bus.emit("task_overdue_detected", t)

        done = by_status.get("done", 0)
        completion_rate = round(done / total * 100, 1) if total else 0.0

        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "overdue": overdue,
            "completion_rate_pct": completion_rate,
        }

    # ------------------------------------------------------------------ #
    #  Persistence helpers                                                  #
    # ------------------------------------------------------------------ #

    def _save(self) -> None:
        self._storage.save(self._tasks)

    def reload(self) -> None:
        self._tasks = self._storage.load()
