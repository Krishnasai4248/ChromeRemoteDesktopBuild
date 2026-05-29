"""Generic file-based storage for Pydantic models with ULID filenames."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, TypeVar, Type, List, Optional

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FileStore(Generic[T]):
    """File-per-entry JSON storage with chronological ULID ordering and eviction.

    Each entry is stored as ``<directory>/<entry.id>.json``. Because ULIDs sort
    lexicographically by creation time, ``sorted(dir.glob("*.json"))`` yields
    entries in chronological order.

    Args:
        directory: Path to the storage directory.
        model_class: Pydantic model class to deserialize entries into.
        max_entries: Maximum entries to retain (oldest evicted first). Default 200.
    """

    def __init__(
        self, directory: Path, model_class: Type[T], max_entries: int = 200
    ) -> None:
        self._directory = directory
        self._model_class = model_class
        self._max_entries = max_entries

    @property
    def directory(self) -> Path:
        """Return the storage directory path."""
        return self._directory

    def save(self, entry: T) -> Path:
        """Persist an entry as a JSON file. Evicts oldest if over capacity.

        Returns the file path written.
        """
        self._directory.mkdir(parents=True, exist_ok=True)
        entry_id = getattr(entry, "id", None)
        if not entry_id:
            raise ValueError("Entry must have an 'id' attribute")
        path = self._directory / f"{entry_id}.json"
        path.write_text(
            json.dumps(entry.model_dump(), indent=2, default=str),
            encoding="utf-8",
        )
        self._evict_if_needed()
        return path

    def load(self, entry_id: str) -> Optional[T]:
        """Load a single entry by ID. Returns None if missing or corrupt."""
        path = self._directory / f"{entry_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._model_class.model_validate(data)
        except (json.JSONDecodeError, OSError, ValueError, KeyError):
            return None

    def list_all(self) -> List[T]:
        """Return all entries in chronological order (oldest first)."""
        if not self._directory.exists():
            return []
        entries: List[T] = []
        for path in sorted(self._directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entry = self._model_class.model_validate(data)
                entries.append(entry)
            except (json.JSONDecodeError, OSError, ValueError, KeyError):
                continue  # Skip corrupt files
        return entries

    def list_recent(self, limit: int = 10) -> List[T]:
        """Return the most recent entries (newest first), up to *limit*."""
        all_entries = self.list_all()
        return list(reversed(all_entries[-limit:]))

    def delete(self, entry_id: str) -> bool:
        """Remove an entry by ID. Returns True if deleted, False if not found."""
        path = self._directory / f"{entry_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def count(self) -> int:
        """Return the number of entries on disk."""
        if not self._directory.exists():
            return 0
        return len(list(self._directory.glob("*.json")))

    def _evict_if_needed(self) -> int:
        """Remove oldest entries if over capacity. Returns count removed."""
        if not self._directory.exists():
            return 0
        files = sorted(self._directory.glob("*.json"))
        overflow = len(files) - self._max_entries
        if overflow <= 0:
            return 0
        for path in files[:overflow]:
            path.unlink(missing_ok=True)
        return overflow
