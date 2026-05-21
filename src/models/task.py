"""Task model — core domain object for the Personal Task Tracker."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def values(cls) -> list[str]:
        return [p.value for p in cls]

    def __lt__(self, other: Priority) -> bool:
        order = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2, Priority.CRITICAL: 3}
        return order[self] < order[other]


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @classmethod
    def values(cls) -> list[str]:
        return [s.value for s in cls]


@dataclass
class Task:
    """Represents a single task record with all associated metadata."""

    title: str
    description: str
    priority: Priority
    category: str
    due_date: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: Status = field(default=Status.TODO)
    created_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    #  Derived properties                                                  #
    # ------------------------------------------------------------------ #

    def is_overdue(self) -> bool:
        """Return True if the task is past its due date and not completed."""
        if self.due_date and self.status not in (Status.DONE, Status.CANCELLED):
            return datetime.now() > self.due_date
        return False

    def matches_keyword(self, keyword: str) -> bool:
        """Return True if keyword appears in title, description, category, or tags."""
        kw = keyword.lower()
        return (
            kw in self.title.lower()
            or kw in self.description.lower()
            or kw in self.category.lower()
            or any(kw in tag.lower() for tag in self.tags)
        )

    # ------------------------------------------------------------------ #
    #  Serialisation                                                       #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "category": self.category,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            priority=Priority(data["priority"]),
            category=data.get("category", "general"),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            status=Status(data.get("status", "todo")),
            created_at=datetime.fromisoformat(data["created_at"]),
            tags=data.get("tags", []),
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Task(id={self.id!r}, title={self.title!r}, "
            f"priority={self.priority.value}, status={self.status.value})"
        )
