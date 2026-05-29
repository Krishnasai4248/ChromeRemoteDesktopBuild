"""Core data models for decision memory and failure pattern recognition."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# ULID generation (Crockford Base32, no external dependency)
# ---------------------------------------------------------------------------

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def generate_id() -> str:
    """Generate a ULID-compatible chronologically sortable unique ID.

    Returns a 26-character string: 10 chars timestamp + 16 chars random,
    encoded in Crockford Base32. IDs sort lexicographically by creation time.
    """
    ts_ms = int(time.time() * 1000)
    random_bytes = os.urandom(10)

    # Encode timestamp (48 bits -> 10 chars)
    ts_chars: list[str] = []
    t = ts_ms
    for _ in range(10):
        ts_chars.append(_CROCKFORD[t & 0x1F])
        t >>= 5
    ts_part = "".join(reversed(ts_chars))

    # Encode random (80 bits -> 16 chars)
    rand_int = int.from_bytes(random_bytes, "big")
    rand_chars: list[str] = []
    for _ in range(16):
        rand_chars.append(_CROCKFORD[rand_int & 0x1F])
        rand_int >>= 5
    rand_part = "".join(reversed(rand_chars))

    return ts_part + rand_part


# ---------------------------------------------------------------------------
# Decision Entry
# ---------------------------------------------------------------------------


class DecisionEntry(BaseModel):
    """Record of an architectural decision with rationale."""

    id: str = Field(
        default_factory=generate_id,
        min_length=26,
        max_length=26,
        description="ULID (26 chars, chronologically sortable)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the decision was made (ISO 8601 UTC)",
    )
    context: str = Field(
        ..., min_length=1, description="What was being done when the decision was made"
    )
    decision: str = Field(..., min_length=1, description="What was chosen")
    alternatives: List[str] = Field(
        default_factory=list, description="Options that were considered"
    )
    rationale: str = Field(
        ..., min_length=1, description="Why this option was selected"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Domain keywords for retrieval",
    )
    agent: str = Field(default="unknown", description="Agent that recorded the decision")
    feature_slug: str = Field(
        default="", description="Feature context (empty if project-level)"
    )

    def to_json_file(self, path: Path) -> None:
        """Serialize this entry to a JSON file."""
        path.write_text(
            json.dumps(self.model_dump(), indent=2, default=str),
            encoding="utf-8",
        )

    @classmethod
    def from_json_file(cls, path: Path) -> "DecisionEntry | None":
        """Deserialize from a JSON file. Returns None on error."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.model_validate(data)
        except (json.JSONDecodeError, OSError, ValueError, KeyError):
            return None


# ---------------------------------------------------------------------------
# Failure Entry
# ---------------------------------------------------------------------------


class FailureEntry(BaseModel):
    """Record of a failed operation with error signature for pattern matching."""

    id: str = Field(
        default_factory=generate_id,
        min_length=26,
        max_length=26,
        description="ULID (26 chars, chronologically sortable)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the failure occurred (ISO 8601 UTC)",
    )
    command: str = Field(
        ..., min_length=1, description="CLI command that was running"
    )
    error_message: str = Field(
        ..., min_length=1, description="Raw error output"
    )
    error_signature: str = Field(
        ..., description="SHA-256 hex of normalized error (64 chars)"
    )
    action_attempted: str = Field(
        ..., min_length=1, description="What the agent/user was trying to do"
    )
    resolution: str = Field(
        default="", description="How the error was fixed (empty if unresolved)"
    )
    resolution_verified: bool = Field(
        default=False, description="True if the resolution was confirmed to work"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Domain keywords for retrieval",
    )
    agent: str = Field(
        default="unknown", description="Agent that encountered the error"
    )
    platform: str = Field(
        ..., min_length=1, description="sys.platform value (win32, linux, darwin)"
    )

    def to_json_file(self, path: Path) -> None:
        """Serialize this entry to a JSON file."""
        path.write_text(
            json.dumps(self.model_dump(), indent=2, default=str),
            encoding="utf-8",
        )

    @classmethod
    def from_json_file(cls, path: Path) -> "FailureEntry | None":
        """Deserialize from a JSON file. Returns None on error."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.model_validate(data)
        except (json.JSONDecodeError, OSError, ValueError, KeyError):
            return None
