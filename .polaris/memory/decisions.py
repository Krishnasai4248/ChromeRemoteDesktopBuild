"""Decision store - domain-specific wrapper around FileStore for architectural decisions."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from specify_cli.memory.models import DecisionEntry, generate_id
from specify_cli.memory.store import FileStore


class DecisionStore:
    """Persistent store for architectural decision records.

    Wraps a ``FileStore[DecisionEntry]`` with domain-specific query methods
    for tag-based filtering and full-text search.

    Args:
        repo_root: Path to the project root (parent of ``.polaris/``).
        max_entries: Maximum entries to retain. Default 200.
    """

    def __init__(self, repo_root: Path, max_entries: int = 200) -> None:
        self._store = FileStore(
            directory=repo_root / ".polaris" / "memory" / "decisions",
            model_class=DecisionEntry,
            max_entries=max_entries,
        )

    @property
    def directory(self) -> Path:
        return self._store.directory

    def record(
        self,
        context: str,
        decision: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        agent: str = "unknown",
        feature_slug: str = "",
    ) -> DecisionEntry:
        """Record a new architectural decision.

        Returns the persisted entry.
        """
        entry = DecisionEntry(
            id=generate_id(),
            timestamp=datetime.now(timezone.utc),
            context=context,
            decision=decision,
            alternatives=alternatives or [],
            rationale=rationale,
            tags=tags or [],
            agent=agent,
            feature_slug=feature_slug,
        )
        self._store.save(entry)
        return entry

    def query_by_tags(self, tags: List[str]) -> List[DecisionEntry]:
        """Return entries whose tags intersect with the given tag list."""
        tag_set = set(tags)
        return [
            entry
            for entry in self._store.list_all()
            if tag_set & set(entry.tags)
        ]

    def search(self, text: str) -> List[DecisionEntry]:
        """Return entries matching a case-insensitive text search.

        Searches in context, decision, and rationale fields.
        """
        needle = text.lower()
        return [
            entry
            for entry in self._store.list_all()
            if needle in entry.context.lower()
            or needle in entry.decision.lower()
            or needle in entry.rationale.lower()
        ]

    def list_all(self) -> List[DecisionEntry]:
        return self._store.list_all()

    def list_recent(self, limit: int = 10) -> List[DecisionEntry]:
        return self._store.list_recent(limit)

    def load(self, entry_id: str) -> Optional[DecisionEntry]:
        return self._store.load(entry_id)

    def delete(self, entry_id: str) -> bool:
        return self._store.delete(entry_id)

    def count(self) -> int:
        return self._store.count()
