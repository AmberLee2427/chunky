"""Chunker for JSON and YAML files using top-level structures."""

from __future__ import annotations

import json
from bisect import bisect_right
from typing import List, Optional, Sequence, Tuple

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import compute_line_boundaries, make_chunk
from .fallback import SlidingWindowChunker


class JSONYamlChunker(Chunker):
    """Split structured config files by top-level objects or keys."""

    def __init__(self, fallback: Optional[Chunker] = None) -> None:
        self._fallback = fallback or SlidingWindowChunker()

    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        content = document.content
        if not content.strip():
            return self._fallback.chunk(document, config)

        try:
            regions = self._split_json(content)
        except ValueError:
            regions = self._split_yaml(content)

        if not regions:
            return self._fallback.chunk(document, config)

        lines = content.splitlines()
        line_starts, line_ends = compute_line_boundaries(lines)

        chunks: List[Chunk] = []
        for start_char, end_char, label in regions:
            if config.max_chunks and len(chunks) >= config.max_chunks:
                break
            start_line = self._char_to_line(start_char, line_starts)
            end_line = self._char_to_line(max(end_char - 1, start_char), line_starts) + 1
            end_line = min(end_line, len(lines))
            if start_line >= end_line:
                continue
            chunks.append(
                make_chunk(
                    document=document,
                    lines=lines,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_index=len(chunks),
                    config=config,
                    line_starts=line_starts,
                    line_ends=line_ends,
                    extra_metadata={"chunk_type": label},
                )
            )

        return chunks or self._fallback.chunk(document, config)

    @staticmethod
    def _split_json(content: str) -> List[Tuple[int, int, str]]:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - guard path
            raise ValueError("invalid json") from exc

        stripped = content.lstrip()
        if not stripped:
            return []
        leading = len(content) - len(stripped)
        first = stripped[0]

        if isinstance(parsed, dict) and first != "{":
            raise ValueError("not JSON object")
        if isinstance(parsed, list) and first != "[":
            raise ValueError("not JSON array")
        if not isinstance(parsed, (dict, list)):
            raise ValueError("unsupported JSON top-level type")

        regions: List[Tuple[int, int, str]] = []
        if isinstance(parsed, dict):
            for start, end in _split_top_level(stripped, opener="{", closer="}"):
                regions.append((leading + start, leading + end, "json_object"))
        else:
            for start, end in _split_top_level(stripped, opener="[", closer="]"):
                regions.append((leading + start, leading + end, "json_item"))
        if not regions:
            raise ValueError("failed to split json")
        return regions

    @staticmethod
    def _split_yaml(content: str) -> List[Tuple[int, int, str]]:
        lines = content.splitlines()
        if not lines:
            return []

        top_level_indices: List[int] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not line.startswith(" "):
                top_level_indices.append(idx)
        if not top_level_indices:
            return []

        top_level_indices = sorted(set(top_level_indices))
        line_starts, _ = compute_line_boundaries(lines)
        regions: List[Tuple[int, int, str]] = []
        for i, start_idx in enumerate(top_level_indices):
            end_idx = top_level_indices[i + 1] if i + 1 < len(top_level_indices) else len(lines)
            start_char = line_starts[start_idx]
            end_char = line_starts[end_idx] if end_idx < len(line_starts) else len(content)
            regions.append((start_char, end_char, "yaml_item"))
        return regions

    @staticmethod
    def _char_to_line(position: int, line_starts: Sequence[int]) -> int:
        idx = bisect_right(line_starts, position)
        if idx == 0:
            return 0
        return idx - 1


def _split_top_level(text: str, opener: str, closer: str) -> List[Tuple[int, int]]:
    if not text or text[0] != opener:
        raise ValueError("unexpected JSON start")
    regions: List[Tuple[int, int]] = []
    depth = 1
    in_string = False
    escape = False
    start = 1  # skip opening char
    for idx in range(1, len(text)):
        char = text[idx]
        if in_string:
            if char == "\\" and not escape:
                escape = True
                continue
            if char == '"' and not escape:
                in_string = False
            escape = False
            continue
        if char == '"':
            in_string = True
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        if depth == 1 and char == ',':
            regions.append((start, idx))
            start = idx + 1
        elif depth == 0 and char == closer:
            regions.append((start, idx))
            break
    return [(s, e) for s, e in regions if s < e]


__all__ = ["JSONYamlChunker"]
