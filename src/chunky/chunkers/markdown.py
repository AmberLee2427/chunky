"""Markdown-aware chunker that groups content by heading hierarchy."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import compute_line_boundaries, make_chunk
from .fallback import SlidingWindowChunker

_HEADING_RE = re.compile(r"^(#{1,6})\s+.+")


class MarkdownHeadingChunker(Chunker):
    """Split markdown documents on top-level headings with optional merging for small sections."""

    def __init__(self, fallback: Optional[Chunker] = None) -> None:
        self._fallback = fallback or SlidingWindowChunker()

    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        lines = document.content.splitlines()
        if not lines:
            return self._fallback.chunk(document, config)

        sections = self._find_sections(lines)
        if not sections:
            return self._fallback.chunk(document, config)

        merged = self._merge_small_sections(sections, min_lines=1)
        line_starts, line_ends = compute_line_boundaries(lines)

        chunks: List[Chunk] = []
        for start, end in merged:
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
                    extra_metadata={"chunk_type": "markdown"},
                )
            )

        return chunks or self._fallback.chunk(document, config)

    @staticmethod
    def _find_sections(lines: List[str]) -> List[Tuple[int, int]]:
        sections: List[Tuple[int, int]] = []
        current_start: Optional[int] = None
        preface_added = False

        for idx, line in enumerate(lines):
            if _HEADING_RE.match(line):
                if current_start is None and idx > 0 and not preface_added:
                    sections.append((0, idx))
                    preface_added = True
                if current_start is not None:
                    sections.append((current_start, idx))
                current_start = idx
        if current_start is not None:
            sections.append((current_start, len(lines)))
        elif lines:
            sections.append((0, len(lines)))
        return [seg for seg in sections if seg[0] < seg[1]]

    @staticmethod
    def _merge_small_sections(
        sections: List[Tuple[int, int]], min_lines: int
    ) -> List[Tuple[int, int]]:
        if len(sections) <= 1:
            return sections

        merged: List[Tuple[int, int]] = []
        buffer_start, buffer_end = sections[0]

        for start, end in sections[1:]:
            if (buffer_end - buffer_start) <= min_lines:
                buffer_end = end
            else:
                merged.append((buffer_start, buffer_end))
                buffer_start, buffer_end = start, end
        merged.append((buffer_start, buffer_end))
        return merged


__all__ = ["MarkdownHeadingChunker"]
