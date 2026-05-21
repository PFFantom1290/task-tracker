"""
Observer pattern — Behavioral.

Allows components to subscribe to task lifecycle events without
coupling the TaskService to any specific notification logic.

Events raised: task_created, task_updated, task_deleted,
               task_overdue_detected
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models.task import Task

# ------------------------------------------------------------------ #
#  Observer interface                                                  #
# ------------------------------------------------------------------ #

class TaskObserver(ABC):
    """Abstract observer that reacts to task events."""

    @abstractmethod
    def on_event(self, event: str, task: Task, **kwargs: Any) -> None:
        ...


# ------------------------------------------------------------------ #
#  Concrete observers                                                  #
# ------------------------------------------------------------------ #

class OverdueNotifier(TaskObserver):
    """Logs a warning whenever an overdue task is detected."""

    def __init__(self):
        self.notifications: list[str] = []

    def on_event(self, event: str, task: Task, **kwargs: Any) -> None:
        if event == "task_overdue_detected":
            msg = f"[OVERDUE] Task '{task.title}' (id={task.id}) is past its due date!"
            self.notifications.append(msg)
            print(msg)


class AuditLogger(TaskObserver):
    """Records every mutating event to an in-memory audit log."""

    def __init__(self):
        self.log: list[dict] = []

    def on_event(self, event: str, task: Task, **kwargs: Any) -> None:
        from datetime import datetime
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "task_id": task.id,
            "task_title": task.title,
        }
        entry.update(kwargs)
        self.log.append(entry)


# ------------------------------------------------------------------ #
#  Subject (event bus)                                                 #
# ------------------------------------------------------------------ #

class TaskEventBus:
    """Holds a list of observers and dispatches events to them."""

    def __init__(self):
        self._observers: list[TaskObserver] = []

    def subscribe(self, observer: TaskObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: TaskObserver) -> None:
        self._observers = [o for o in self._observers if o is not observer]

    def emit(self, event: str, task: Task, **kwargs: Any) -> None:
        for obs in self._observers:
            obs.on_event(event, task, **kwargs)
