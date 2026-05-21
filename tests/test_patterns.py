"""
Additional tests for Observer and Command patterns.
Boosts coverage of src/patterns/observer.py and src/patterns/command.py.
"""


import pytest

from src.models.task import Priority, Task
from src.patterns.command import CommandHistory, DeleteCommand, UpdateCommand
from src.patterns.observer import AuditLogger, OverdueNotifier, TaskEventBus
from src.services.task_service import TaskService
from src.storage.json_storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    return TaskService(storage=JsonStorage(tmp_path / "cmd.json"))


# ── Observer tests ────────────────────────────────────────────────────

class TestObserver:

    def _make_task(self):
        return Task(title="T", description="", priority=Priority.LOW, category="c")

    def test_overdue_notifier_records_message(self):
        notifier = OverdueNotifier()
        task = self._make_task()
        notifier.on_event("task_overdue_detected", task)
        assert len(notifier.notifications) == 1
        assert "OVERDUE" in notifier.notifications[0]

    def test_overdue_notifier_ignores_other_events(self):
        notifier = OverdueNotifier()
        task = self._make_task()
        notifier.on_event("task_created", task)
        assert len(notifier.notifications) == 0

    def test_audit_logger_records_event(self):
        logger = AuditLogger()
        task = self._make_task()
        logger.on_event("task_created", task)
        assert len(logger.log) == 1
        assert logger.log[0]["event"] == "task_created"
        assert logger.log[0]["task_id"] == task.id

    def test_event_bus_dispatches_to_all_subscribers(self):
        bus = TaskEventBus()
        logger = AuditLogger()
        notifier = OverdueNotifier()
        bus.subscribe(logger)
        bus.subscribe(notifier)

        task = self._make_task()
        bus.emit("task_created", task)
        assert len(logger.log) == 1

    def test_event_bus_unsubscribe(self):
        bus = TaskEventBus()
        logger = AuditLogger()
        bus.subscribe(logger)
        bus.unsubscribe(logger)

        task = self._make_task()
        bus.emit("task_created", task)
        assert len(logger.log) == 0

    def test_event_bus_no_duplicate_subscribe(self):
        bus = TaskEventBus()
        logger = AuditLogger()
        bus.subscribe(logger)
        bus.subscribe(logger)  # duplicate
        task = self._make_task()
        bus.emit("task_created", task)
        assert len(logger.log) == 1  # dispatched once


# ── Command tests ─────────────────────────────────────────────────────

class TestCommandPattern:

    def test_delete_command_execute_and_undo(self, service):
        task = service.create("To delete")
        history = CommandHistory()
        cmd = DeleteCommand(service, task.id)
        history.execute(cmd)
        # Task is gone
        assert service.list_all() == []
        # Undo restores it
        history.undo()
        assert len(service.list_all()) == 1
        assert service.list_all()[0].title == "To delete"

    def test_update_command_execute_and_undo(self, service):
        task = service.create("Original")
        history = CommandHistory()
        cmd = UpdateCommand(service, task.id, {"title": "Updated"})
        history.execute(cmd)
        assert service.get_by_id(task.id).title == "Updated"
        history.undo()
        assert service.get_by_id(task.id).title == "Original"

    def test_undo_empty_history_returns_false(self):
        history = CommandHistory()
        assert history.undo() is False

    def test_command_history_clear(self, service):
        task = service.create("T")
        history = CommandHistory()
        history.execute(UpdateCommand(service, task.id, {"title": "New"}))
        history.clear()
        assert history.undo() is False

    def test_multiple_undo_steps(self, service):
        task = service.create("A")
        history = CommandHistory()
        history.execute(UpdateCommand(service, task.id, {"title": "B"}))
        history.execute(UpdateCommand(service, task.id, {"title": "C"}))
        history.undo()
        assert service.get_by_id(task.id).title == "B"
        history.undo()
        assert service.get_by_id(task.id).title == "A"
