"""Helper utilities shared by chunker implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..types import Chunk, ChunkerConfig, Document


def compute_line_boundaries(lines: List[str]) -> tuple[List[int], List[int]]:
    """Return lists of starting and ending character offsets per line."""

    starts: List[int] = []
    ends: List[int] = []
    cursor = 0
    for idx, line in enumerate(lines):
        if idx > 0:
            cursor += 1  # newline before this line
        starts.append(cursor)
        cursor += len(line)
        ends.append(cursor)
    return starts, ends


def build_chunk_id(path: Path, index: int) -> str:
    return f"{path}::chunk-{index}"


def make_chunk(
    *,
    document: Document,
    lines: List[str],
    start_line: int,
    end_line: int,
    chunk_index: int,
    config: ChunkerConfig,
    line_starts: List[int],
    line_ends: List[int],
    extra_metadata: Optional[Dict[str, object]] = None,
) -> Chunk:
    """Create a chunk from the given line span."""

    text = "\n".join(lines[start_line:end_line])
    span_start = line_starts[start_line] if start_line < len(line_starts) else 0
    span_end = line_ends[end_line - 1] if end_line - 1 < len(line_ends) else span_start

    metadata: Dict[str, object] = {
        "chunk_index": chunk_index,
        "line_start": start_line + 1,
        "line_end": end_line,
        "span_start": span_start,
        "span_end": span_end,
    }
    if config.metadata:
        metadata.update(config.metadata)
    if extra_metadata:
        metadata.update(extra_metadata)

    return Chunk(
        chunk_id=build_chunk_id(document.path, chunk_index),
        text=text,
        source_document=document.path,
        metadata=metadata,
    )
