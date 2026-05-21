"""
Tests for the Task domain model.

BLACK-BOX tests (derived from the specification, no internal knowledge):
  - BB-01  Task with all fields stores them correctly
  - BB-02  Task without optional fields uses sensible defaults
  - BB-03  is_overdue returns True for past-due active task
  - BB-04  is_overdue returns False for completed task even if past due
  - BB-05  matches_keyword searches across title, description, category, tags

WHITE-BOX tests (derived from code structure / branch coverage):
  - WB-01  is_overdue returns False when due_date is None (None-branch)
  - WB-02  is_overdue returns False when status is CANCELLED (status-branch)
  - WB-03  matches_keyword is case-insensitive (lowercase normalisation path)
  - WB-04  to_dict / from_dict round-trip preserves all fields
  - WB-05  from_dict with missing optional keys falls back to defaults
"""

from datetime import datetime

import pytest

from src.models.task import Priority, Status, Task

# ================================================================== #
#  Fixtures                                                            #
# ================================================================== #

@pytest.fixture
def sample_task() -> Task:
    return Task(
        title="Buy groceries",
        description="Milk, eggs, bread",
        priority=Priority.MEDIUM,
        category="personal",
        due_date=datetime(2025, 12, 31),
        tags=["shopping", "weekly"],
    )


@pytest.fixture
def overdue_task() -> Task:
    return Task(
        title="Submit report",
        description="Q3 report",
        priority=Priority.HIGH,
        category="work",
        due_date=datetime(2000, 1, 1),  # far in the past
    )


# ================================================================== #
#  BLACK-BOX tests (BB)                                               #
# ================================================================== #

class TestTaskBlackBox:
    """BB: Tests derived purely from the public specification."""

    def test_bb01_all_fields_stored_correctly(self, sample_task):
        """BB-01: Constructor stores every supplied field."""
        assert sample_task.title == "Buy groceries"
        assert sample_task.description == "Milk, eggs, bread"
        assert sample_task.priority == Priority.MEDIUM
        assert sample_task.category == "personal"
        assert sample_task.due_date == datetime(2025, 12, 31)
        assert "shopping" in sample_task.tags

    def test_bb02_default_fields(self):
        """BB-02: Optional fields have sensible defaults."""
        task = Task(title="Simple", description="", priority=Priority.LOW, category="misc")
        assert task.status == Status.TODO
        assert task.due_date is None
        assert task.tags == []
        assert len(task.id) == 8

    def test_bb03_is_overdue_past_due(self, overdue_task):
        """BB-03: Active task with past due date is overdue."""
        assert overdue_task.is_overdue() is True

    def test_bb04_done_task_not_overdue(self, overdue_task):
        """BB-04: Done task is never considered overdue."""
        overdue_task.status = Status.DONE
        assert overdue_task.is_overdue() is False

    def test_bb05_matches_keyword_finds_in_title(self, sample_task):
        """BB-05: Keyword found in title returns True."""
        assert sample_task.matches_keyword("groceries") is True

    def test_bb05b_matches_keyword_finds_in_description(self, sample_task):
        """BB-05: Keyword found in description returns True."""
        assert sample_task.matches_keyword("bread") is True

    def test_bb05c_matches_keyword_finds_in_tags(self, sample_task):
        """BB-05: Keyword found in tags returns True."""
        assert sample_task.matches_keyword("shopping") is True

    def test_bb05d_matches_keyword_not_found(self, sample_task):
        """BB-05: Keyword absent from all fields returns False."""
        assert sample_task.matches_keyword("zzz_not_found_zzz") is False


# ================================================================== #
#  WHITE-BOX tests (WB)                                               #
# ================================================================== #

class TestTaskWhiteBox:
    """
    WB: Tests derived from code structure (branch coverage).

    Technique: Branch coverage — every branch of every conditional
    in task.py is exercised at least once.
    """

    def test_wb01_is_overdue_no_due_date(self, sample_task):
        """WB-01: None branch — no due_date → never overdue."""
        sample_task.due_date = None
        assert sample_task.is_overdue() is False

    def test_wb02_is_overdue_cancelled(self, overdue_task):
        """WB-02: Status-branch — CANCELLED task is not overdue."""
        overdue_task.status = Status.CANCELLED
        assert overdue_task.is_overdue() is False

    def test_wb03_matches_keyword_case_insensitive(self, sample_task):
        """WB-03: Lowercase normalisation path — uppercase keyword matches."""
        assert sample_task.matches_keyword("GROCERIES") is True

    def test_wb04_to_dict_from_dict_roundtrip(self, sample_task):
        """WB-04: Serialisation round-trip preserves every field."""
        d = sample_task.to_dict()
        restored = Task.from_dict(d)
        assert restored.id == sample_task.id
        assert restored.title == sample_task.title
        assert restored.priority == sample_task.priority
        assert restored.status == sample_task.status
        assert restored.due_date == sample_task.due_date
        assert restored.tags == sample_task.tags

    def test_wb05_from_dict_missing_optional_keys(self):
        """WB-05: Missing optional keys in dict fall back to defaults."""
        minimal = {
            "id": "abc12345",
            "title": "Test",
            "description": "",
            "priority": "low",
            "created_at": datetime.now().isoformat(),
        }
        task = Task.from_dict(minimal)
        assert task.category == "general"
        assert task.status == Status.TODO
        assert task.due_date is None
        assert task.tags == []

    def test_wb06_to_dict_none_due_date(self):
        """WB-06: due_date=None serialises to None in dict."""
        task = Task(title="X", description="", priority=Priority.LOW, category="c")
        d = task.to_dict()
        assert d["due_date"] is None

    def test_wb07_priority_ordering(self):
        """WB-07: Priority enum ordering LOW < MEDIUM < HIGH < CRITICAL."""
        assert Priority.LOW < Priority.MEDIUM
        assert Priority.MEDIUM < Priority.HIGH
        assert Priority.HIGH < Priority.CRITICAL

    def test_wb08_matches_keyword_in_category(self):
        """WB-08: Category branch is covered."""
        task = Task(title="X", description="", priority=Priority.LOW, category="finance")
        assert task.matches_keyword("finance") is True
