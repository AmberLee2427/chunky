"""Lightweight Fortran chunker based on subroutine/function boundaries."""

from __future__ import annotations

import re
from typing import List, Optional

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import compute_line_boundaries, make_chunk
from .fallback import SlidingWindowChunker

_FORTRAN_START_RE = re.compile(r"^\s*(subroutine|function|program)\b", re.IGNORECASE)
_FORTRAN_END_RE = re.compile(r"^\s*end\b", re.IGNORECASE)


class FortranChunker(Chunker):
    """Chunk Fortran sources by subroutine/function blocks."""

    def __init__(self, fallback: Optional[Chunker] = None) -> None:
        self.fallback = fallback or SlidingWindowChunker()

    def chunk(self, document: Document, config: ChunkerConfig) -> List[Chunk]:
        lines = document.content.splitlines()
        if not lines:
            return self.fallback.chunk(document, config)

        boundaries: List[tuple[int, int]] = []
        current_start: Optional[int] = None
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("!"):
                continue
            if current_start is None and _FORTRAN_START_RE.match(stripped):
                current_start = idx
                continue
            if current_start is not None and _FORTRAN_END_RE.match(stripped):
                boundaries.append((current_start, idx + 1))
                current_start = None
        if current_start is not None:
            boundaries.append((current_start, len(lines)))

        if not boundaries:
            return self.fallback.chunk(document, config)

        line_starts, line_ends = compute_line_boundaries(lines)
        chunks: List[Chunk] = []
        for start, end in boundaries:
            if config.max_chunks and len(chunks) >= config.max_chunks:
                break
            chunk = make_chunk(
                document=document,
                lines=lines,
                start_line=start,
                end_line=end,
                chunk_index=len(chunks),
                config=config,
                line_starts=line_starts,
                line_ends=line_ends,
                extra_metadata={"chunk_type": "fortran"},
            )
            chunks.append(chunk)

        return chunks or self.fallback.chunk(document, config)


__all__ = ["FortranChunker"]
