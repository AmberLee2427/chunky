"""Tree-sitter backed chunkers for structured languages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import compute_line_boundaries, make_chunk
from .fallback import SlidingWindowChunker

try:  # pragma: no cover - optional dependency guard
    from tree_sitter import Parser
    from tree_sitter_languages import get_language
except ImportError:  # pragma: no cover - handled at runtime
    Parser = None  # type: ignore
    get_language = None  # type: ignore


@dataclass(slots=True)
class TreeSitterSpec:
    """Configuration describing how to chunk a language with Tree-sitter."""

    language: str
    query: str
    capture_name: str = "chunk"
    metadata: Optional[Dict[str, str]] = None


class TreeSitterChunker(Chunker):
    """Chunker that uses Tree-sitter queries to extract structural spans."""

    def __init__(self, spec: TreeSitterSpec, fallback: Optional[Chunker] = None) -> None:
        self.spec = spec
        self.fallback = fallback or SlidingWindowChunker()
        self._available = False
        self._parser = None
        self._query = None

        parser_cls = Parser
        get_lang = get_language
        if parser_cls is None or get_lang is None:
            try:  # retry import if dependencies were installed after module import
                from tree_sitter import Parser as _Parser  # type: ignore
                from tree_sitter_languages import get_language as _get_language  # type: ignore
            except Exception:  # pragma: no cover - still unavailable
                return
            parser_cls = _Parser
            get_lang = _get_language

        try:
            language = get_lang(spec.language)
        except Exception:  # pragma: no cover - missing grammar
            return

        parser = parser_cls()
        parser.set_language(language)
        try:
            query = language.query(spec.query)
        except Exception:  # pragma: no cover - invalid query
            return

        self._available = True
        self._parser = parser
        self._query = query

    def chunk(self, document: Document, config: ChunkerConfig) -> List[Chunk]:
        if not self._available or self._parser is None or self._query is None:
            return self.fallback.chunk(document, config)

        source = document.content
        if not source.strip():
            return self.fallback.chunk(document, config)

        try:
            tree = self._parser.parse(source.encode("utf-8"))
        except Exception:  # pragma: no cover - parser error
            return self.fallback.chunk(document, config)

        captures = self._query.captures(tree.root_node)
        ranges = _select_ranges(captures, self.spec.capture_name)
        if not ranges:
            return self.fallback.chunk(document, config)

        lines = source.splitlines()
        line_starts, line_ends = compute_line_boundaries(lines)

        chunks: List[Chunk] = []
        for start_line, end_line in ranges:
            if config.max_chunks and len(chunks) >= config.max_chunks:
                break
            chunk = make_chunk(
                document=document,
                lines=lines,
                start_line=start_line,
                end_line=end_line,
                chunk_index=len(chunks),
                config=config,
                line_starts=line_starts,
                line_ends=line_ends,
                extra_metadata=self.spec.metadata or {"chunk_type": self.spec.language},
            )
            chunks.append(chunk)

        return chunks or self.fallback.chunk(document, config)


def _select_ranges(captures: Iterable[tuple], capture_name: str) -> List[tuple[int, int]]:
    """Normalise Tree-sitter captures into unique line ranges."""

    ranges: List[tuple[int, int]] = []
    for node, name in captures:
        if name != capture_name:
            continue
        start = node.start_point[0]
        end = node.end_point[0] + 1
        if ranges and start < ranges[-1][1]:
            # Extend previous range if overlapping to avoid tiny fragments
            prev_start, prev_end = ranges[-1]
            ranges[-1] = (prev_start, max(prev_end, end))
        else:
            ranges.append((start, max(start + 1, end)))
    return ranges


__all__ = ["TreeSitterSpec", "TreeSitterChunker"]
