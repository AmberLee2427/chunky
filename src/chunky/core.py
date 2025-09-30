"""Core interfaces and exceptions for chunkers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .types import Chunk, ChunkerConfig, Document


class ChunkingError(RuntimeError):
    """Raised when a chunker cannot process the provided document."""


@runtime_checkable
class Chunker(Protocol):
    """Protocol implemented by all chunkers."""

    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        """Return a list of chunks for the given document."""


__all__ = ["ChunkingError", "Chunker"]
