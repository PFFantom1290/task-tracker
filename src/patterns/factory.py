"""
Factory Method pattern — Creational.

Provides a unified interface for creating different Task variants.
The concrete factories (StandardTaskFactory, RecurringTaskFactory,
SubTaskFactory) each override `create()` to return a properly
configured Task without exposing construction details to callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from src.models.task import Priority, Task

# ------------------------------------------------------------------ #
#  Abstract creator                                                    #
# ------------------------------------------------------------------ #

class TaskFactory(ABC):
    """Abstract factory that declares the factory method."""

    @abstractmethod
    def create(
        self,
        title: str,
        description: str,
        priority: str,
        category: str,
        due_date: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        """Factory method — subclasses decide which Task variant to build."""
        ...

    # Template method that uses the factory method
    def create_and_validate(self, **kwargs) -> Task:
        task = self.create(**kwargs)
        if not task.title.strip():
            raise ValueError("Task title cannot be empty.")
        if task.priority not in Priority:
            raise ValueError(f"Invalid priority: {task.priority}")
        return task


# ------------------------------------------------------------------ #
#  Concrete creators                                                   #
# ------------------------------------------------------------------ #

class StandardTaskFactory(TaskFactory):
    """Creates a plain one-off task — the default variant."""

    def create(
        self,
        title: str,
        description: str,
        priority: str,
        category: str,
        due_date: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        return Task(
            title=title,
            description=description,
            priority=Priority(priority),
            category=category,
            due_date=due_date,
            tags=tags or [],
        )


class RecurringTaskFactory(TaskFactory):
    """Creates a recurring task — automatically appends [recurring] tag."""

    def __init__(self, interval_days: int = 7):
        self._interval_days = interval_days

    def create(
        self,
        title: str,
        description: str,
        priority: str,
        category: str,
        due_date: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        base_tags = list(tags or [])
        if "recurring" not in base_tags:
            base_tags.append("recurring")
        effective_due = due_date or (datetime.now() + timedelta(days=self._interval_days))
        return Task(
            title=title,
            description=f"[Recurring every {self._interval_days}d] {description}",
            priority=Priority(priority),
            category=category,
            due_date=effective_due,
            tags=base_tags,
        )


class SubTaskFactory(TaskFactory):
    """Creates a sub-task linked to a parent task via tags."""

    def __init__(self, parent_id: str):
        self._parent_id = parent_id

    def create(
        self,
        title: str,
        description: str,
        priority: str,
        category: str,
        due_date: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        base_tags = list(tags or [])
        parent_tag = f"parent:{self._parent_id}"
        if parent_tag not in base_tags:
            base_tags.append(parent_tag)
        return Task(
            title=title,
            description=description,
            priority=Priority(priority),
            category=category,
            due_date=due_date,
            tags=base_tags,
        )


# ------------------------------------------------------------------ #
#  Registry / convenience getter                                       #
# ------------------------------------------------------------------ #

def get_factory(task_type: str, **kwargs) -> TaskFactory:
    """Return the appropriate factory for *task_type*."""
    factories: dict[str, type[TaskFactory]] = {
        "standard": StandardTaskFactory,
        "recurring": RecurringTaskFactory,
        "subtask": SubTaskFactory,
    }
    if task_type not in factories:
        raise ValueError(f"Unknown task type '{task_type}'. Choose from: {list(factories)}")
    if task_type == "recurring":
        interval = kwargs.get("interval_days", 7)
        return RecurringTaskFactory(interval_days=interval)
    if task_type == "subtask":
        parent_id = kwargs.get("parent_id", "")
        return SubTaskFactory(parent_id=parent_id)
    return StandardTaskFactory()
