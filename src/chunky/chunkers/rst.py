"""reStructuredText chunker that uses section heading boundaries."""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import (
    compute_line_boundaries,
    enforce_max_chars,
    finalize_chunks,
    make_chunk,
    resolve_doc_id,
)
from .fallback import SlidingWindowChunker

_RST_HEADING_CHARS = set("=-~^\"'`#*+:")


class RSTChunker(Chunker):
    """Split RST documents by section heading structure."""

    def __init__(self, fallback: Optional[Chunker] = None) -> None:
        self._fallback = fallback or SlidingWindowChunker()

    def chunk(self, document: Document, config: ChunkerConfig) -> List[Chunk]:
        lines = document.content.splitlines()
        if not lines:
            return self._annotate_fallback(document, config)

        sections = self._find_sections(lines)
        if not sections:
            return self._annotate_fallback(document, config)

        avoid_boundaries = self._directive_boundaries(lines)
        sections = enforce_max_chars(lines, sections, config, avoid_boundaries=avoid_boundaries)
        if not sections:
            return self._annotate_fallback(document, config)

        line_starts, line_ends = compute_line_boundaries(lines)
        doc_id = resolve_doc_id(document, config)

        chunks: List[Chunk] = []
        for start, end in sections:
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
                    doc_id=doc_id,
                    chunk_id_template=config.chunk_id_template,
                    extra_metadata={"chunk_type": "rst"},
                )
            )

        if not chunks:
            return self._annotate_fallback(document, config)

        finalize_chunks(chunks, doc_id)
        return chunks

    def _annotate_fallback(self, document: Document, config: ChunkerConfig) -> List[Chunk]:
        chunks = self._fallback.chunk(document, config)
        for chunk in chunks:
            chunk.metadata["chunk_type"] = "rst"
        return chunks

    @classmethod
    def _find_sections(cls, lines: List[str]) -> List[Tuple[int, int]]:
        starts: List[int] = []
        idx = 0
        line_count = len(lines)

        while idx < line_count:
            if idx + 2 < line_count and cls._is_overline_heading(lines, idx):
                starts.append(idx)
                idx += 3
                continue
            if idx + 1 < line_count and cls._is_underline_heading(lines, idx):
                starts.append(idx)
                idx += 2
                continue
            idx += 1

        starts = sorted(set(starts))
        if not starts:
            return []

        sections: List[Tuple[int, int]] = []
        if starts[0] > 0:
            sections.append((0, starts[0]))
        for pos, start in enumerate(starts):
            end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
            if start < end:
                sections.append((start, end))
        return sections

    @classmethod
    def _is_underline_heading(cls, lines: List[str], title_idx: int) -> bool:
        title = lines[title_idx].strip()
        if not title:
            return False

        underline = lines[title_idx + 1].strip()
        underline_char = cls._heading_marker(underline)
        if underline_char is None:
            return False
        return len(underline) >= len(title)

    @classmethod
    def _is_overline_heading(cls, lines: List[str], overline_idx: int) -> bool:
        overline = lines[overline_idx].strip()
        title = lines[overline_idx + 1].strip()
        underline = lines[overline_idx + 2].strip()
        if not title:
            return False

        over_char = cls._heading_marker(overline)
        under_char = cls._heading_marker(underline)
        if over_char is None or under_char is None or over_char != under_char:
            return False
        return len(overline) >= len(title) and len(underline) >= len(title)

    @staticmethod
    def _heading_marker(line: str) -> Optional[str]:
        if not line:
            return None
        marker = line[0]
        if marker not in _RST_HEADING_CHARS:
            return None
        if any(char != marker for char in line):
            return None
        return marker

    @staticmethod
    def _directive_boundaries(lines: List[str]) -> Set[int]:
        """Return split boundaries to avoid inside RST directive blocks."""

        avoid: Set[int] = set()
        in_directive = False
        directive_indent = 0

        for idx, line in enumerate(lines[:-1]):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if stripped.startswith(".. "):
                in_directive = True
                directive_indent = indent
                avoid.add(idx + 1)
                continue

            if in_directive:
                if not stripped:
                    avoid.add(idx + 1)
                    continue
                if indent > directive_indent:
                    avoid.add(idx + 1)
                    continue
                in_directive = False

        return avoid


__all__ = ["RSTChunker"]
