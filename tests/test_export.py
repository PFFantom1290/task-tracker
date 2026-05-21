"""
Tests for ExportService, JsonStorage, and design-pattern units.

BLACK-BOX:
  BB-11  JSON export produces valid JSON with all tasks
  BB-12  CSV export produces correct column headers
  BB-13  Storage survives empty file gracefully
  BB-14  Factory produces correct task variant

WHITE-BOX:
  WB-19  ExportService raises for unsupported format
  WB-20  CsvExporter encodes tags as pipe-separated string
  WB-21  JsonStorage handles corrupt JSON without crash
  WB-22  CompositeFilter applies all sub-filters (AND semantics)
  WB-23  SortByPriority orders LOW→CRITICAL correctly
  WB-24  FilterByDateRange excludes tasks outside window
"""

import csv
import json
from datetime import datetime, timedelta

import pytest

from src.models.task import Priority, Status, Task
from src.patterns.factory import (
    RecurringTaskFactory,
    StandardTaskFactory,
    SubTaskFactory,
    get_factory,
)
from src.patterns.strategy import (
    CompositeFilter,
    FilterByDateRange,
    FilterByPriority,
    FilterByStatus,
    SortByPriority,
)
from src.services.export_service import ExportService
from src.storage.json_storage import JsonStorage

# ================================================================== #
#  Helpers                                                             #
# ================================================================== #

def make_task(title="Task", priority="medium", due_days=None, tags=None, status="todo") -> Task:
    due = datetime.now() + timedelta(days=due_days) if due_days is not None else None
    t = Task(
        title=title,
        description="desc",
        priority=Priority(priority),
        category="cat",
        due_date=due,
        tags=tags or [],
    )
    t.status = Status(status)
    return t


# ================================================================== #
#  ExportService — BLACK-BOX                                           #
# ================================================================== #

class TestExportBlackBox:

    def test_bb11_json_export_valid(self, tmp_path):
        """BB-11: JSON export creates a parseable file with all tasks."""
        tasks = [make_task("A"), make_task("B")]
        path = ExportService.export(tasks, "json", tmp_path / "out.json")
        data = json.loads(path.read_text())
        assert len(data) == 2
        assert data[0]["title"] == "A"

    def test_bb12_csv_has_correct_headers(self, tmp_path):
        """BB-12: CSV export includes the expected column headers."""
        tasks = [make_task("X")]
        path = ExportService.export(tasks, "csv", tmp_path / "out.csv")
        with path.open() as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        assert "id" in headers
        assert "title" in headers
        assert "priority" in headers
        assert "tags" in headers


# ================================================================== #
#  ExportService — WHITE-BOX                                           #
# ================================================================== #

class TestExportWhiteBox:

    def test_wb19_unsupported_format_raises(self, tmp_path):
        """WB-19: Requesting an unknown format hits the ValueError branch."""
        with pytest.raises(ValueError, match="Unsupported format"):
            ExportService.export([], "xml", tmp_path / "out.xml")

    def test_wb20_csv_tags_pipe_separated(self, tmp_path):
        """WB-20: Tags list is serialised as pipe-separated values."""
        tasks = [make_task("T", tags=["a", "b", "c"])]
        path = ExportService.export(tasks, "csv", tmp_path / "out.csv")
        with path.open() as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["tags"] == "a|b|c"

    def test_wb20b_csv_no_tags(self, tmp_path):
        """WB-20b: Empty tags list serialises to empty string."""
        tasks = [make_task("T")]
        path = ExportService.export(tasks, "csv", tmp_path / "out.csv")
        with path.open() as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["tags"] == ""


# ================================================================== #
#  JsonStorage — BLACK-BOX & WHITE-BOX                                #
# ================================================================== #

class TestJsonStorage:

    def test_bb13_load_missing_file_returns_empty(self, tmp_path):
        """BB-13: Loading a non-existent file returns an empty dict."""
        storage = JsonStorage(tmp_path / "nonexistent.json")
        assert storage.load() == {}

    def test_save_and_load_roundtrip(self, tmp_path):
        """Round-trip: saved tasks are loadable."""
        storage = JsonStorage(tmp_path / "tasks.json")
        task = make_task("Round-trip")
        storage.save({task.id: task})
        loaded = storage.load()
        assert task.id in loaded
        assert loaded[task.id].title == "Round-trip"

    def test_wb21_corrupt_json_returns_empty(self, tmp_path):
        """WB-21: Corrupt JSON file is handled gracefully (except branch)."""
        p = tmp_path / "bad.json"
        p.write_text("not valid json!!!")
        storage = JsonStorage(p)
        assert storage.load() == {}

    def test_delete_file(self, tmp_path):
        """delete_file() removes the file from disk."""
        p = tmp_path / "del.json"
        storage = JsonStorage(p)
        storage.save({})
        assert p.exists()
        storage.delete_file()
        assert not p.exists()


# ================================================================== #
#  Strategy pattern                                                    #
# ================================================================== #

class TestStrategies:

    def test_wb22_composite_filter_and_semantics(self):
        """WB-22: CompositeFilter keeps only tasks matching ALL filters."""
        tasks = [
            make_task("HP-todo", priority="high", status="todo"),
            make_task("HP-done", priority="high", status="done"),
            make_task("LP-todo", priority="low", status="todo"),
        ]
        cf = CompositeFilter(FilterByPriority("high"), FilterByStatus("todo"))
        result = cf.apply(tasks)
        assert len(result) == 1
        assert result[0].title == "HP-todo"

    def test_wb23_sort_by_priority_ascending(self):
        """WB-23: SortByPriority orders LOW → CRITICAL."""
        tasks = [make_task(p, priority=p) for p in ["critical", "low", "high", "medium"]]
        sorted_tasks = SortByPriority().sort(tasks, reverse=False)
        priorities = [t.priority.value for t in sorted_tasks]
        assert priorities == ["low", "medium", "high", "critical"]

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


# ================================================================== #
#  Factory pattern                                                     #
# ================================================================== #

class TestFactoryPattern:

    def test_bb14_standard_factory(self):
        """BB-14: StandardTaskFactory creates a plain task."""
        factory = StandardTaskFactory()
        task = factory.create("T", "", "medium", "cat")
        assert task.title == "T"
        assert "recurring" not in task.tags

    def test_recurring_factory_adds_tag(self):
        """RecurringTaskFactory adds 'recurring' tag."""
        factory = RecurringTaskFactory(interval_days=3)
        task = factory.create("Recur", "", "low", "cat")
        assert "recurring" in task.tags

    def test_recurring_factory_sets_due_date_if_absent(self):
        """RecurringTaskFactory auto-assigns due date when none given."""
        factory = RecurringTaskFactory(interval_days=7)
        task = factory.create("Recur", "", "low", "cat", due_date=None)
        assert task.due_date is not None

    def test_subtask_factory_adds_parent_tag(self):
        """SubTaskFactory adds parent:<id> tag."""
        factory = SubTaskFactory(parent_id="abc123")
        task = factory.create("Sub", "", "medium", "cat")
        assert "parent:abc123" in task.tags

    def test_get_factory_unknown_type_raises(self):
        """get_factory() raises ValueError for unknown type."""
        with pytest.raises(ValueError, match="Unknown task type"):
            get_factory("invalid_type")
