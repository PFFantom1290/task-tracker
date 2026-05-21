"""
Acceptance tests (ATDD/BDD style) — Given-When-Then format.

These tests are written from the USER's perspective, treating the
system as a black box and verifying complete user scenarios.

Scenarios:
  AT-01  User creates a high-priority task and it appears in listings
  AT-02  User filters by priority to see only critical tasks
  AT-03  User marks a task done and the completion rate improves
  AT-04  User searches by keyword and finds the right task
  AT-05  User exports tasks and gets valid output files
  AT-06  User updates a task and sees the change persisted
  AT-07  User deletes a task and it no longer appears
  AT-08  User views overdue statistics
"""

import json
from datetime import datetime, timedelta

import pytest

from src.models.task import Priority
from src.patterns.strategy import FilterByPriority
from src.services.export_service import ExportService
from src.services.task_service import TaskService
from src.storage.json_storage import JsonStorage

# ================================================================== #
#  Shared fixture                                                      #
# ================================================================== #

@pytest.fixture
def service(tmp_path):
    storage = JsonStorage(tmp_path / "acceptance.json")
    return TaskService(storage=storage)


# ================================================================== #
#  AT-01  Create and list                                              #
# ================================================================== #

class TestAT01CreateAndList:
    """
    Given: an empty task list
    When:  the user creates a HIGH-priority task
    Then:  the task appears in list_all() with correct priority
    """

    def test_create_task_appears_in_list(self, service):
        # Given
        assert service.list_all() == []

        # When
        service.create("Fix production bug", priority="high", category="work")

        # Then
        tasks = service.list_all()
        assert len(tasks) == 1
        assert tasks[0].title == "Fix production bug"
        assert tasks[0].priority == Priority.HIGH


# ================================================================== #
#  AT-02  Filter by priority                                           #
# ================================================================== #

class TestAT02FilterByPriority:
    """
    Given: tasks with mixed priorities
    When:  user filters by priority=critical
    Then:  only critical tasks are shown
    """

    def test_filter_shows_only_matching_priority(self, service):
        # Given
        service.create("Low task", priority="low")
        service.create("Medium task", priority="medium")
        service.create("Critical task", priority="critical")

        # When
        results = service.list_all(filters=[FilterByPriority("critical")])

        # Then
        assert len(results) == 1
        assert results[0].title == "Critical task"


# ================================================================== #
#  AT-03  Mark done and check completion rate                          #
# ================================================================== #

class TestAT03CompletionRate:
    """
    Given: 4 tasks, all TODO
    When:  user marks 2 of them as DONE
    Then:  completion_rate_pct is 50%
    """

    def test_completion_rate_updates_after_done(self, service):
        # Given
        tasks = [service.create(f"Task {i}") for i in range(4)]

        # When
        service.update(tasks[0].id, status="done")
        service.update(tasks[1].id, status="done")

        # Then
        stats = service.statistics()
        assert stats["completion_rate_pct"] == pytest.approx(50.0)


# ================================================================== #
#  AT-04  Keyword search                                               #
# ================================================================== #

class TestAT04KeywordSearch:
    """
    Given: multiple tasks with different content
    When:  user searches for "invoice"
    Then:  only the task containing "invoice" is returned
    """

    def test_search_returns_only_matching_task(self, service):
        # Given
        service.create("Write unit tests", category="engineering")
        service.create("Send invoice to client", description="Q3 invoice", category="finance")
        service.create("Team meeting", category="admin")

        # When
        results = service.search("invoice")

        # Then
        assert len(results) == 1
        assert "invoice" in results[0].title.lower() or "invoice" in results[0].description.lower()


# ================================================================== #
#  AT-05  Export produces valid files                                  #
# ================================================================== #

class TestAT05Export:
    """
    Given: a non-empty task list
    When:  user exports to JSON and CSV
    Then:  both files exist and contain the expected data
    """

    def test_export_json_and_csv(self, service, tmp_path):
        # Given
        service.create("Task Alpha", priority="high")
        service.create("Task Beta", priority="low")
        tasks = service.list_all()

        # When
        json_path = ExportService.export(tasks, "json", tmp_path / "export.json")
        csv_path = ExportService.export(tasks, "csv", tmp_path / "export.csv")

        # Then — JSON
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert len(data) == 2

        # Then — CSV
        assert csv_path.exists()
        lines = csv_path.read_text().splitlines()
        assert len(lines) == 3  # header + 2 rows


# ================================================================== #
#  AT-06  Update and persist                                           #
# ================================================================== #

class TestAT06UpdateAndPersist:
    """
    Given: a task stored on disk
    When:  user updates its title and a new service instance is loaded
    Then:  the new title is visible in the fresh instance
    """

    def test_update_is_persisted(self, tmp_path):
        # Given
        storage = JsonStorage(tmp_path / "persist.json")
        svc1 = TaskService(storage=storage)
        task = svc1.create("Original title")

        # When
        svc1.update(task.id, title="Updated title")

        # Then — reload from disk
        svc2 = TaskService(storage=storage)
        reloaded = svc2.get_by_id(task.id)
        assert reloaded.title == "Updated title"


# ================================================================== #
#  AT-07  Delete                                                       #
# ================================================================== #

class TestAT07Delete:
    """
    Given: a task in the list
    When:  user deletes it
    Then:  the list is empty and the task ID is no longer found
    """

    def test_delete_removes_from_list(self, service):
        # Given
        task = service.create("Delete me")
        assert len(service.list_all()) == 1

        # When
        service.delete(task.id)

        # Then
        assert service.list_all() == []


# ================================================================== #
#  AT-08  Overdue statistics                                           #
# ================================================================== #

class TestAT08OverdueStats:
    """
    Given: a task with a past due date and a task with a future due date
    When:  user requests statistics
    Then:  only 1 overdue task is reported
    """

    def test_only_past_due_counted_as_overdue(self, service):
        # Given
        past = datetime.now() - timedelta(days=5)
        future = datetime.now() + timedelta(days=10)
        service.create("Overdue task", due_date=past)
        service.create("Future task", due_date=future)

        # When
        stats = service.statistics()

        # Then
        assert stats["overdue"] == 1
