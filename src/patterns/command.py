"""
Command pattern — Behavioral (bonus).

Wraps task mutations as Command objects so that an undo stack can
reverse any operation without the CLI needing to know the details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.task_service import TaskService


class Command(ABC):
    """Abstract command."""

    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...


class DeleteCommand(Command):
    """Deletes a task; undo re-creates it."""

    def __init__(self, service: TaskService, task_id: str):
        self._service = service
        self._task_id = task_id
        self._snapshot = None

    def execute(self) -> None:
        self._snapshot = self._service.get_by_id(self._task_id)
        self._service.delete(self._task_id)

    def undo(self) -> None:
        if self._snapshot:
            self._service._tasks[self._snapshot.id] = self._snapshot
            self._service._save()


class UpdateCommand(Command):
    """Updates a task; undo restores the previous state."""

    def __init__(self, service: TaskService, task_id: str, updates: dict):
        self._service = service
        self._task_id = task_id
        self._updates = updates
        self._before = None

    def execute(self) -> None:
        task = self._service.get_by_id(self._task_id)
        # Snapshot the *original* field values for undo
        self._before = {k: getattr(task, k) for k in self._updates}
        self._service.update(self._task_id, **self._updates)

    def undo(self) -> None:
        if self._before is not None:
            self._service.update(self._task_id, **self._before)


class CommandHistory:
    """Manages the executed-command stack for undo support."""

    def __init__(self):
        self._stack: list[Command] = []

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        self._stack.append(cmd)

    def undo(self) -> bool:
        if not self._stack:
            return False
        self._stack.pop().undo()
        return True

    def clear(self) -> None:
        self._stack.clear()
