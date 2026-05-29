"""Error message normalization and signature computation.

Normalizes error messages by replacing variable content (paths, line numbers,
timestamps, UUIDs, etc.) with stable placeholders, then computes a SHA-256
hash of the normalized text. Two errors that differ only in variable parts
(e.g., different file paths or line numbers) produce the same signature.
"""

from __future__ import annotations

import hashlib
import re

# Compiled normalization patterns (applied in order)
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Windows paths: C:\Users\dev\project\file.py
    (re.compile(r"[A-Za-z]:\\[\w\\/.\-]+"), "<PATH>"),
    # Unix paths with extension: /home/user/project/file.py
    (re.compile(r"/[\w/\-]+\.\w+"), "<PATH>"),
    # ISO timestamps: 2026-04-15T14:30:00Z or 2026-04-15 14:30:00
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\s]*"), "<TIMESTAMP>"),
    # UUIDs: 550e8400-e29b-41d4-a716-446655440000
    (
        re.compile(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        ),
        "<UUID>",
    ),
    # ULIDs: 26 chars of Crockford Base32
    (re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b"), "<ULID>"),
    # Line numbers: line 42
    (re.compile(r"line \d+"), "line <N>"),
    # Temp directories: tmpxyz123
    (re.compile(r"tmp[a-zA-Z0-9_]+"), "<TMPDIR>"),
    # Numeric sequences (4+ digits): port 54321, pid 12345
    (re.compile(r"\b\d{4,}\b"), "<NUM>"),
]


def normalize_error(error_message: str) -> str:
    """Normalize an error message by replacing variable content with placeholders.

    Args:
        error_message: Raw error message text.

    Returns:
        Normalized text with paths, line numbers, timestamps, UUIDs, and other
        variable content replaced by stable placeholder tokens.
    """
    result = error_message
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result.strip()


def compute_signature(error_message: str) -> str:
    """Compute a deterministic SHA-256 signature for an error message.

    The message is first normalized (variable content stripped), then hashed.
    Two errors that differ only in variable parts produce the same signature.

    Args:
        error_message: Raw error message text.

    Returns:
        64-character lowercase hex string (SHA-256 digest).
    """
    normalized = normalize_error(error_message)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
