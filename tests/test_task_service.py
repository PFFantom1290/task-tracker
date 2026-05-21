"""
Tests for TaskService.

BLACK-BOX (specification-derived):
  BB-06  create() returns a Task with the right fields
  BB-07  list_all() returns all tasks
  BB-08  delete() removes the task
  BB-09  search() finds matching tasks
  BB-10  statistics() returns correct counts

WHITE-BOX (structure-derived, branch coverage):
  WB-09  update() raises ValueError for disallowed field
  WB-10  get_by_id() raises TaskNotFoundError for unknown id
  WB-11  list_all() with sort + filter chains correctly
  WB-12  statistics() overdue detection branch
  WB-13  create() with tags=None defaults to []
"""

from datetime import datetime

import pytest

from src.models.task import Priority, Status
from src.patterns.strategy import FilterByPriority, SortByPriority
from src.services.task_service import TaskNotFoundError, TaskService
from src.storage.json_storage import JsonStorage

# ================================================================== #
#  Fixtures                                                            #
# ================================================================== #

@pytest.fixture
def in_memory_service(tmp_path):
    """TaskService backed by a temp-directory JSON file."""
    storage = JsonStorage(tmp_path / "test_tasks.json")
    return TaskService(storage=storage)


# ================================================================== #
#  BLACK-BOX tests                                                     #
# ================================================================== #

class TestTaskServiceBlackBox:

    def test_bb06_create_returns_task(self, in_memory_service):
        """BB-06: create() returns a properly populated Task."""
        task = in_memory_service.create("Test Task", priority="high", category="work")
        assert task.title == "Test Task"
        assert task.priority == Priority.HIGH
        assert task.category == "work"

    def test_bb07_list_all_returns_all(self, in_memory_service):
        """BB-07: list_all() returns every created task."""
        in_memory_service.create("A")
        in_memory_service.create("B")
        in_memory_service.create("C")
        tasks = in_memory_service.list_all()
        assert len(tasks) == 3

    def test_bb08_delete_removes_task(self, in_memory_service):
        """BB-08: delete() removes the task; subsequent get raises."""
        task = in_memory_service.create("Delete me")
        in_memory_service.delete(task.id)
        with pytest.raises(TaskNotFoundError):
            in_memory_service.get_by_id(task.id)

    def test_bb09_search_finds_by_keyword(self, in_memory_service):
        """BB-09: search() finds tasks matching the keyword."""
        in_memory_service.create("Buy milk", description="grocery run", category="home")
        in_memory_service.create("Write report", category="work")
        results = in_memory_service.search("milk")
        assert len(results) == 1
        assert results[0].title == "Buy milk"

    def test_bb10_statistics_counts(self, in_memory_service):
        """BB-10: statistics() returns accurate aggregate counts."""
        in_memory_service.create("T1", priority="high")
        in_memory_service.create("T2", priority="low")
        t3 = in_memory_service.create("T3", priority="high")
        in_memory_service.update(t3.id, status="done")
        stats = in_memory_service.statistics()
        assert stats["total"] == 3
        assert stats["by_priority"].get("high") == 2
        assert stats["by_status"].get("done") == 1
        assert stats["completion_rate_pct"] == pytest.approx(33.3, abs=0.2)


# ================================================================== #
#  WHITE-BOX tests                                                     #
# ================================================================== #

class TestTaskServiceWhiteBox:

    def test_wb09_update_invalid_field_raises(self, in_memory_service):
        """WB-09: update() raises ValueError for unknown field (guard branch)."""
        task = in_memory_service.create("T")
        with pytest.raises(ValueError, match="Cannot update field"):
            in_memory_service.update(task.id, nonexistent_field="value")

    def test_wb10_get_by_id_unknown_raises(self, in_memory_service):
        """WB-10: get_by_id() raises TaskNotFoundError (None-check branch)."""
        with pytest.raises(TaskNotFoundError):
            in_memory_service.get_by_id("does_not_exist")

    def test_wb11_list_with_sort_and_filter(self, in_memory_service):
        """WB-11: list_all() correctly chains sort + filter."""
        in_memory_service.create("Low", priority="low")
        in_memory_service.create("High", priority="high")
        in_memory_service.create("Critical", priority="critical")

        tasks = in_memory_service.list_all(
            sort_strategy=SortByPriority(),
            reverse=True,
            filters=[FilterByPriority("high")],
        )
        assert len(tasks) == 1
        assert tasks[0].title == "High"

    def test_wb12_statistics_overdue_detection(self, in_memory_service):
        """WB-12: statistics() counts overdue tasks via is_overdue() branch."""
        past = datetime(2000, 1, 1)
        in_memory_service.create("Late", due_date=past)
        stats = in_memory_service.statistics()
        assert stats["overdue"] == 1

    def test_wb13_create_with_no_tags_defaults_to_empty(self, in_memory_service):
        """WB-13: tags=None in create() results in empty list."""
        task = in_memory_service.create("No tags", tags=None)
        assert task.tags == []

    def test_wb14_update_priority_as_string(self, in_memory_service):
        """WB-14: update() auto-converts string priority to Priority enum."""
        task = in_memory_service.create("T")
        updated = in_memory_service.update(task.id, priority="critical")
        assert updated.priority == Priority.CRITICAL

    def test_wb15_update_status_as_string(self, in_memory_service):
        """WB-15: update() auto-converts string status to Status enum."""
        task = in_memory_service.create("T")
        updated = in_memory_service.update(task.id, status="in_progress")
        assert updated.status == Status.IN_PROGRESS

    def test_wb16_reload_syncs_from_storage(self, tmp_path):
        """WB-16: reload() re-reads the storage file."""
        storage = JsonStorage(tmp_path / "reload.json")
        svc = TaskService(storage=storage)
        svc.create("Persisted Task")
        svc2 = TaskService(storage=storage)
        svc2.reload()
        assert len(svc2.list_all()) == 1

    def test_wb17_search_empty_returns_empty(self, in_memory_service):
        """WB-17: search() on empty store returns []."""
        assert in_memory_service.search("anything") == []

    def test_wb18_statistics_empty_store(self, in_memory_service):
        """WB-18: statistics() on empty store gives zero completion rate."""
        stats = in_memory_service.statistics()
        assert stats["total"] == 0
        assert stats["completion_rate_pct"] == 0.0
