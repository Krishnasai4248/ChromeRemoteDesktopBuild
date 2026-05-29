"""Decision memory and failure pattern recognition for Polaris.

Provides persistent memory layers that record architectural decisions
and failure patterns across sessions, enabling agents to reference
prior reasoning and avoid known pitfalls.
"""

from specify_cli.memory.models import DecisionEntry, FailureEntry
from specify_cli.memory.store import FileStore
from specify_cli.memory.signature import normalize_error, compute_signature

__all__ = [
    "DecisionEntry",
    "FailureEntry",
    "FileStore",
    "normalize_error",
    "compute_signature",
]
