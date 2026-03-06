"""Chunker for nb4llm notebook exports (``.nb.txt``)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import (
    compute_line_boundaries,
    compute_line_length_prefix,
    enforce_max_chars,
    finalize_chunks,
    make_chunk,
    resolve_doc_id,
    span_char_length,
)
from .markdown import MarkdownHeadingChunker

_CELL_FENCE_RE = re.compile(r"^```(python|markdown)\s*$")
_FENCE_CLOSE = "```"


@dataclass
class _NotebookCell:
    cell_type: str
    start_line: int
    end_line: int


@dataclass
class _NotebookChunkSpec:
    start_line: int
    end_line: int
    cell_types: List[str]
    last_cell_type: str


class NotebookChunker(Chunker):
    """Chunk notebook exports by grouping markdown and code cell blocks."""

    def __init__(self, fallback: Optional[Chunker] = None) -> None:
        self._fallback = fallback or MarkdownHeadingChunker()

    def chunk(self, document: Document, config: ChunkerConfig) -> List[Chunk]:
        lines = document.content.splitlines()
        if not lines:
            return self._annotate_fallback(document, config)

        cells = self._parse_cells(lines)
        if not cells:
            return self._annotate_fallback(document, config)

        merged = self._merge_cells(cells, lines, config.max_chars)
        if not merged:
            return self._annotate_fallback(document, config)

        line_starts, line_ends = compute_line_boundaries(lines)
        doc_id = resolve_doc_id(document, config)

        chunks: List[Chunk] = []
        for spec in merged:
            segments = enforce_max_chars(
                lines,
                [(spec.start_line, spec.end_line)],
                config,
            )
            for start, end in segments:
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
                        extra_metadata={
                            "chunk_type": "notebook",
                            "cell_types": list(spec.cell_types),
                        },
                    )
                )
            if config.max_chunks and len(chunks) >= config.max_chunks:
                break

        if not chunks:
            return self._annotate_fallback(document, config)

        finalize_chunks(chunks, doc_id)
        return chunks

    def _annotate_fallback(self, document: Document, config: ChunkerConfig) -> List[Chunk]:
        chunks = self._fallback.chunk(document, config)
        for chunk in chunks:
            chunk.metadata["chunk_type"] = "notebook"
            chunk.metadata["cell_types"] = ["markdown"]
        return chunks

    @staticmethod
    def _parse_cells(lines: List[str]) -> List[_NotebookCell]:
        cells: List[_NotebookCell] = []
        line_count = len(lines)
        idx = 0
        cursor = 0

        while idx < line_count:
            match = _CELL_FENCE_RE.match(lines[idx])
            if not match:
                idx += 1
                continue

            if cursor < idx and any(line.strip() for line in lines[cursor:idx]):
                cells.append(_NotebookCell("markdown", cursor, idx))

            cell_type = match.group(1)
            start_line = idx
            idx += 1
            while idx < line_count and lines[idx].strip() != _FENCE_CLOSE:
                idx += 1

            if idx >= line_count:
                return []

            end_line = idx + 1
            cells.append(_NotebookCell(cell_type, start_line, end_line))
            cursor = end_line
            idx = end_line

        if cursor < line_count and any(line.strip() for line in lines[cursor:line_count]):
            cells.append(_NotebookCell("markdown", cursor, line_count))

        return cells

    @staticmethod
    def _merge_cells(
        cells: List[_NotebookCell],
        lines: List[str],
        max_chars: int,
    ) -> List[_NotebookChunkSpec]:
        if not cells:
            return []

        max_chars = max(1, max_chars)
        prefix = compute_line_length_prefix(lines)
        merged: List[_NotebookChunkSpec] = []
        current = _NotebookChunkSpec(
            start_line=cells[0].start_line,
            end_line=cells[0].end_line,
            cell_types=[cells[0].cell_type],
            last_cell_type=cells[0].cell_type,
        )

        for cell in cells[1:]:
            if cell.cell_type == "markdown":
                if current.last_cell_type == "markdown":
                    current.end_line = cell.end_line
                    if "markdown" not in current.cell_types:
                        current.cell_types.append("markdown")
                    current.last_cell_type = "markdown"
                    continue
                merged.append(current)
                current = _NotebookChunkSpec(
                    start_line=cell.start_line,
                    end_line=cell.end_line,
                    cell_types=["markdown"],
                    last_cell_type="markdown",
                )
                continue

            candidate_end = cell.end_line
            candidate_len = span_char_length(prefix, current.start_line, candidate_end)
            if candidate_len <= max_chars:
                current.end_line = candidate_end
                if cell.cell_type not in current.cell_types:
                    current.cell_types.append(cell.cell_type)
                current.last_cell_type = cell.cell_type
                continue

            merged.append(current)
            current = _NotebookChunkSpec(
                start_line=cell.start_line,
                end_line=cell.end_line,
                cell_types=[cell.cell_type],
                last_cell_type=cell.cell_type,
            )

        merged.append(current)
        return merged


__all__ = ["NotebookChunker"]
