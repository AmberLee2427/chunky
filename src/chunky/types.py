"""Core data structures for the semantic chunking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Document:
    """Normalized representation of a file to be chunked."""

    path: Path
    content: str
    language: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunk of text ready for downstream indexing."""

    chunk_id: str
    text: str
    source_document: Path
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkerConfig:
    """Configuration shared across chunkers."""

    max_chars: int = 2000
    lines_per_chunk: int = 120
    line_overlap: int = 20
    max_chunks: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clamp_lines(self, lines: int) -> int:
        """Clamp the requested line count to a sensible positive value."""

        return max(1, lines)

    def clamp_overlap(self, overlap: int, window: int) -> int:
        """Clamp overlap so it cannot exceed the window size."""

        overlap = max(0, overlap)
        return min(overlap, max(0, window - 1))
