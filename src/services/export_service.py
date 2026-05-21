"""
ExportService — Template Method pattern.

`BaseExporter` defines the export skeleton (open → write header → write rows → close).
`JsonExporter` and `CsvExporter` override only the format-specific steps.
This avoids code duplication while keeping format details localised.
"""

from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TextIO

from src.models.task import Task

# ------------------------------------------------------------------ #
#  Abstract exporter (Template Method)                                #
# ------------------------------------------------------------------ #

class BaseExporter(ABC):
    """Defines the export algorithm skeleton."""

    def export(self, tasks: list[Task], path: str | Path) -> Path:
        """Public entry point — calls the template method steps."""
        dest = Path(path)
        with dest.open("w", encoding="utf-8", newline="") as fh:
            self._write_header(fh, tasks)
            self._write_rows(fh, tasks)
        return dest

    @abstractmethod
    def _write_header(self, fh: TextIO, tasks: list[Task]) -> None:
        ...

    @abstractmethod
    def _write_rows(self, fh: TextIO, tasks: list[Task]) -> None:
        ...

    @property
    @abstractmethod
    def extension(self) -> str:
        ...


# ------------------------------------------------------------------ #
#  Concrete exporters                                                  #
# ------------------------------------------------------------------ #

class JsonExporter(BaseExporter):
    """Exports tasks as a pretty-printed JSON array."""

    @property
    def extension(self) -> str:
        return ".json"

    def _write_header(self, fh: TextIO, tasks: list[Task]) -> None:
        pass  # JSON has no separate header

    def _write_rows(self, fh: TextIO, tasks: list[Task]) -> None:
        payload = [t.to_dict() for t in tasks]
        json.dump(payload, fh, indent=2, ensure_ascii=False)


class CsvExporter(BaseExporter):
    """Exports tasks as a UTF-8 CSV file."""

    _COLUMNS = [
        "id", "title", "description", "priority", "category",
        "status", "due_date", "created_at", "tags",
    ]

    @property
    def extension(self) -> str:
        return ".csv"

    def _write_header(self, fh: TextIO, tasks: list[Task]) -> None:
        writer = csv.DictWriter(fh, fieldnames=self._COLUMNS)
        writer.writeheader()
        # Stash writer for use in _write_rows
        self._writer = writer

    def _write_rows(self, fh: TextIO, tasks: list[Task]) -> None:
        for task in tasks:
            row = task.to_dict()
            row["tags"] = "|".join(row["tags"])
            self._writer.writerow(row)


# ------------------------------------------------------------------ #
#  Convenience facade                                                  #
# ------------------------------------------------------------------ #

class ExportService:
    """Facade that routes to the correct exporter by format name."""

    _EXPORTERS: dict[str, BaseExporter] = {
        "json": JsonExporter(),
        "csv": CsvExporter(),
    }

    @classmethod
    def export(cls, tasks: list[Task], fmt: str, path: str | Path) -> Path:
        fmt = fmt.lower()
        if fmt not in cls._EXPORTERS:
            raise ValueError(f"Unsupported format '{fmt}'. Choose from: {list(cls._EXPORTERS)}")
        return cls._EXPORTERS[fmt].export(tasks, path)

    @classmethod
    def supported_formats(cls) -> list[str]:
        return list(cls._EXPORTERS.keys())
