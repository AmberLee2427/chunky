"""Plain text chunker that groups paragraphs."""

from __future__ import annotations

from typing import List, Optional

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import compute_line_boundaries, make_chunk
from .fallback import SlidingWindowChunker


class PlainTextChunker(Chunker):
    """Split plain text on blank-line separated paragraphs."""

    def __init__(self, fallback: Optional[Chunker] = None) -> None:
        self._fallback = fallback or SlidingWindowChunker()

    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        lines = document.content.splitlines()
        if not lines:
            return self._fallback.chunk(document, config)

        paragraphs = self._find_paragraphs(lines)
        if not paragraphs:
            return self._fallback.chunk(document, config)

        combined = self._combine_by_window(paragraphs, config.lines_per_chunk)
        line_starts, line_ends = compute_line_boundaries(lines)

        chunks: List[Chunk] = []
        for start, end in combined:
            if config.max_chunks and len(chunks) >= config.max_chunks:
                break
            chunks.append(
                make_chunk(
                    document=document,
                    lines=lines,
                    start_line=start,
                    end_line=end,
                    chunk_index=len(chunks),
                    config=config,
                    line_starts=line_starts,
                    line_ends=line_ends,
                    extra_metadata={"chunk_type": "text"},
                )
            )

        return chunks or self._fallback.chunk(document, config)

    @staticmethod
    def _find_paragraphs(lines: List[str]) -> List[tuple[int, int]]:
        paragraphs: List[tuple[int, int]] = []
        start = 0
        for idx, line in enumerate(lines):
            if line.strip():
                continue
            if start < idx:
                paragraphs.append((start, idx))
            start = idx + 1
        if start < len(lines):
            paragraphs.append((start, len(lines)))
        return paragraphs

    @staticmethod
    def _combine_by_window(
        paragraphs: List[tuple[int, int]], max_lines: int
    ) -> List[tuple[int, int]]:
        if max_lines <= 0:
            return paragraphs

        combined: List[tuple[int, int]] = []
        current_start, current_end = paragraphs[0]
        for start, end in paragraphs[1:]:
            if (end - current_start) <= max_lines:
                current_end = end
            else:
                combined.append((current_start, current_end))
                current_start, current_end = start, end
        combined.append((current_start, current_end))
        return combined


__all__ = ["PlainTextChunker"]
