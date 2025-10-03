"""Python-aware chunker that splits on top-level definitions."""

from __future__ import annotations

import ast
from typing import List, Optional

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import compute_line_boundaries, make_chunk
from .fallback import SlidingWindowChunker


class PythonSemanticChunker(Chunker):
    """Split Python source on module docstring and top-level definitions."""

    def __init__(self, fallback: Optional[Chunker] = None) -> None:
        self._fallback = fallback or SlidingWindowChunker()

    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        if not document.content.strip():
            return self._fallback.chunk(document, config)

        lines = document.content.splitlines()
        line_starts, line_ends = compute_line_boundaries(lines)

        try:
            tree = ast.parse(document.content)
        except SyntaxError:
            return self._fallback.chunk(document, config)

        segments: List[tuple[int, int]] = []
        previous_end = 0
        for index, node in enumerate(tree.body):
            start = getattr(node, "lineno", None)
            if start is None:
                continue
            end = getattr(node, "end_lineno", None)
            if end is None:
                end = self._approximate_end(node, tree.body, index, len(lines))
            if end is None:
                return self._fallback.chunk(document, config)

            start -= 1
            end = min(end, len(lines))
            if previous_end < start:
                segments.append((previous_end, start))
            segments.append((start, end))
            previous_end = end

        if previous_end < len(lines):
            segments.append((previous_end, len(lines)))

        # Filter empty segments
        segments = [seg for seg in segments if seg[0] < seg[1]]
        if not segments:
            return self._fallback.chunk(document, config)

        chunks = []
        for start, end in segments:
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
                extra_metadata={"chunk_type": "python"},
            )
            chunks.append(chunk)

        if not chunks:
            return self._fallback.chunk(document, config)
        return chunks

    @staticmethod
    def _approximate_end(
        node: ast.AST, siblings: List[ast.AST], index: int, line_count: int
    ) -> Optional[int]:
        """Best-effort end line when AST node lacks ``end_lineno``."""

        for sibling in siblings[index + 1 :]:
            sibling_lineno = getattr(sibling, "lineno", None)
            if sibling_lineno is not None:
                return max(sibling_lineno - 1, 0)
        return line_count


__all__ = ["PythonSemanticChunker"]
