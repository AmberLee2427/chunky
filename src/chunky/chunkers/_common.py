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


def resolve_doc_id(document: Document, config: ChunkerConfig) -> str:
    value = document.metadata.get(config.doc_id_key)
    if value is None or value == "":
        return document.path.as_posix()
    return str(value)


def build_chunk_id(doc_id: str, index: int, template: str, path: Path) -> str:
    return template.format(doc_id=doc_id, index=index, path=path.as_posix())


def finalize_chunks(chunks: List[Chunk], doc_id: str) -> None:
    total = len(chunks)
    for chunk in chunks:
        chunk.metadata["chunk_count"] = total
        chunk.metadata.setdefault("source_document", doc_id)


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
    doc_id: str,
    chunk_id_template: str,
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
        "source_document": doc_id,
    }
    if config.metadata:
        metadata.update(config.metadata)
    if extra_metadata:
        metadata.update(extra_metadata)

    return Chunk(
        chunk_id=build_chunk_id(doc_id, chunk_index, chunk_id_template, document.path),
        text=text,
        source_document=doc_id,
        metadata=metadata,
    )
