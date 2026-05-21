"""
JSON file-based persistence layer.

Acts as an Adapter between the domain model (Task) and the raw JSON
storage format, keeping I/O concerns entirely separate from business logic.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.models.task import Task


class JsonStorage:
    """Reads and writes tasks from/to a JSON file."""

    def __init__(self, path: str | Path = "tasks.json"):
        self._path = Path(path)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def load(self) -> dict[str, Task]:
        """Load all tasks from disk; returns an empty dict if file is absent."""
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
            data: list[dict] = json.loads(raw)
            return {item["id"]: Task.from_dict(item) for item in data}
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupt file — start fresh rather than crash
            return {}

    def save(self, tasks: dict[str, Task]) -> None:
        """Persist all tasks to disk atomically (write-to-tmp then rename)."""
        payload = [t.to_dict() for t in tasks.values()]
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)

    def delete_file(self) -> None:
        """Remove the storage file (used in tests)."""
        if self._path.exists():
            self._path.unlink()
