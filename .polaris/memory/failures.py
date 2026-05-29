"""Failure store - domain-specific wrapper for failure pattern tracking and resolution."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from specify_cli.memory.models import FailureEntry, generate_id
from specify_cli.memory.signature import compute_signature
from specify_cli.memory.store import FileStore


class FailureStore:
    """Persistent store for failure records with error signature matching.

    Wraps a ``FileStore[FailureEntry]`` with signature-based deduplication,
    resolution attachment, and query methods.

    Args:
        repo_root: Path to the project root (parent of ``.polaris/``).
        max_entries: Maximum entries to retain. Default 200.
    """

    def __init__(self, repo_root: Path, max_entries: int = 200) -> None:
        self._store = FileStore(
            directory=repo_root / ".polaris" / "memory" / "failures",
            model_class=FailureEntry,
            max_entries=max_entries,
        )

    @property
    def directory(self) -> Path:
        return self._store.directory

    def record(
        self,
        command: str,
        error_message: str,
        action_attempted: str,
        tags: Optional[List[str]] = None,
        agent: str = "unknown",
        platform: Optional[str] = None,
    ) -> Tuple[FailureEntry, Optional[str]]:
        """Record a new failure. Returns (entry, known_fix_or_None).

        Auto-computes the error signature. If a resolved entry with the same
        signature already exists, returns the known resolution as the second
        element so the caller can display it.
        """
        signature = compute_signature(error_message)
        plat = platform or sys.platform

        # Check for existing resolution with the same signature
        known_fix = self._find_resolution(signature)

        entry = FailureEntry(
            id=generate_id(),
            timestamp=datetime.now(timezone.utc),
            command=command,
            error_message=error_message,
            error_signature=signature,
            action_attempted=action_attempted,
            tags=tags or [],
            agent=agent,
            platform=plat,
        )
        self._store.save(entry)
        return entry, known_fix

    def resolve(
        self,
        entry_id: Optional[str] = None,
        signature: Optional[str] = None,
        resolution: str = "",
        verified: bool = True,
    ) -> int:
        """Attach a resolution to failure entries.

        Provide either ``entry_id`` (resolves one entry) or ``signature``
        (resolves all unresolved entries with that signature).

        Returns the count of entries updated.
        """
        updated = 0

        if entry_id:
            entry = self._store.load(entry_id)
            if entry is not None:
                updated += self._update_entry(entry, resolution, verified)

        elif signature:
            for entry in self._store.list_all():
                if entry.error_signature == signature and not entry.resolution:
                    updated += self._update_entry(entry, resolution, verified)

        return updated

    def query_by_signature(self, signature: str) -> List[FailureEntry]:
        """Return entries matching the given error signature."""
        return [
            e for e in self._store.list_all()
            if e.error_signature == signature
        ]

    def query_by_platform(self, platform: str) -> List[FailureEntry]:
        """Return entries matching the given platform."""
        return [
            e for e in self._store.list_all()
            if e.platform == platform
        ]

    def query_by_tags(self, tags: List[str]) -> List[FailureEntry]:
        """Return entries whose tags intersect with the given tag list."""
        tag_set = set(tags)
        return [
            e for e in self._store.list_all()
            if tag_set & set(e.tags)
        ]

    def get_unresolved(self) -> List[FailureEntry]:
        """Return entries that have no resolution."""
        return [e for e in self._store.list_all() if not e.resolution]

    def get_resolved(self) -> List[FailureEntry]:
        """Return entries that have a resolution."""
        return [e for e in self._store.list_all() if e.resolution]

    def list_all(self) -> List[FailureEntry]:
        return self._store.list_all()

    def list_recent(self, limit: int = 10) -> List[FailureEntry]:
        return self._store.list_recent(limit)

    def load(self, entry_id: str) -> Optional[FailureEntry]:
        return self._store.load(entry_id)

    def delete(self, entry_id: str) -> bool:
        return self._store.delete(entry_id)

    def count(self) -> int:
        return self._store.count()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_resolution(self, signature: str) -> Optional[str]:
        """Find an existing verified resolution for a signature."""
        for entry in self._store.list_all():
            if (
                entry.error_signature == signature
                and entry.resolution
                and entry.resolution_verified
            ):
                return entry.resolution
        return None

    def _update_entry(
        self, entry: FailureEntry, resolution: str, verified: bool
    ) -> int:
        """Update a single entry's resolution and re-save it."""
        updated_data = entry.model_dump()
        updated_data["resolution"] = resolution
        updated_data["resolution_verified"] = verified
        updated_entry = FailureEntry.model_validate(updated_data)
        self._store.save(updated_entry)
        return 1
