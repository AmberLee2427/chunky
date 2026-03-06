"""Helper utilities shared by chunker implementations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from ..types import Chunk, ChunkerConfig, Document

_SENTENCE_END_RE = re.compile(r"[.!?][\"')\]]*$")
_DEFAULT_SECONDARY_WINDOW = 40


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


def compute_line_length_prefix(lines: Sequence[str]) -> List[int]:
    """Return prefix sums of line lengths for O(1) span-size lookups."""

    prefix: List[int] = [0]
    for line in lines:
        prefix.append(prefix[-1] + len(line))
    return prefix


def span_char_length(prefix: Sequence[int], start_line: int, end_line: int) -> int:
    """Return ``len('\\n'.join(lines[start_line:end_line]))`` using length prefixes."""

    if end_line <= start_line:
        return 0
    text_chars = prefix[end_line] - prefix[start_line]
    newline_chars = max(0, end_line - start_line - 1)
    return text_chars + newline_chars


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


def enforce_max_chars(
    lines: List[str],
    segments: Sequence[Tuple[int, int]],
    config: ChunkerConfig,
    *,
    avoid_boundaries: Optional[Set[int]] = None,
) -> List[Tuple[int, int]]:
    """Split any oversized segment using ``_secondary_split``."""

    max_chars = max(1, config.max_chars)
    prefix = compute_line_length_prefix(lines)
    expanded: List[Tuple[int, int]] = []

    for start, end in segments:
        if start >= end:
            continue
        if span_char_length(prefix, start, end) <= max_chars:
            expanded.append((start, end))
            continue

        relative_avoid: Optional[Set[int]] = None
        if avoid_boundaries:
            relative_avoid = {
                boundary - start for boundary in avoid_boundaries if start < boundary < end
            }

        split_ranges = _secondary_split(
            lines[start:end],
            max_chars,
            lines_per_chunk=config.lines_per_chunk,
            avoid_boundaries=relative_avoid,
        )
        if not split_ranges:
            expanded.append((start, end))
            continue
        expanded.extend(
            (start + split_start, start + split_end)
            for split_start, split_end in split_ranges
            if split_start < split_end
        )
    return expanded


def _secondary_split(
    lines: List[str],
    max_chars: int,
    *,
    lines_per_chunk: int = _DEFAULT_SECONDARY_WINDOW,
    avoid_boundaries: Optional[Set[int]] = None,
) -> List[Tuple[int, int]]:
    """Split oversized text by blank lines, then sentence ends, then line windows."""

    if not lines:
        return []

    max_chars = max(1, max_chars)
    window = max(1, lines_per_chunk)
    line_count = len(lines)
    prefix = compute_line_length_prefix(lines)

    if span_char_length(prefix, 0, line_count) <= max_chars:
        return [(0, line_count)]

    blank_boundaries = [idx + 1 for idx, line in enumerate(lines[:-1]) if not line.strip()]
    sentence_boundaries = [
        idx + 1
        for idx, line in enumerate(lines[:-1])
        if _SENTENCE_END_RE.search(line.rstrip()) is not None
    ]

    preferred = blank_boundaries if blank_boundaries else sentence_boundaries
    secondary = sentence_boundaries if blank_boundaries else []
    avoid = avoid_boundaries or set()

    chunks: List[Tuple[int, int]] = []
    start = 0
    while start < line_count:
        if span_char_length(prefix, start, start + 1) > max_chars:
            chunks.append((start, start + 1))
            start += 1
            continue

        max_end = _max_span_end(prefix, start, line_count, max_chars)
        if max_end >= line_count:
            chunks.append((start, line_count))
            break

        split = _pick_boundary(preferred, start, max_end, avoid)
        if split is None and secondary:
            split = _pick_boundary(secondary, start, max_end, avoid)
        if split is None:
            split = min(max_end, start + window)
            if split <= start:
                split = max_end

        chunks.append((start, split))
        start = split

    return [chunk for chunk in chunks if chunk[0] < chunk[1]]


def _max_span_end(
    prefix: Sequence[int],
    start_line: int,
    line_count: int,
    max_chars: int,
) -> int:
    """Return the greatest end-line index that fits within ``max_chars``."""

    end = start_line + 1
    while end < line_count and span_char_length(prefix, start_line, end + 1) <= max_chars:
        end += 1
    return end


def _pick_boundary(
    boundaries: Sequence[int],
    start_line: int,
    max_end: int,
    avoid_boundaries: Set[int],
) -> Optional[int]:
    """Pick the right-most boundary, preferring positions not marked as avoided."""

    preferred: Optional[int] = None
    fallback: Optional[int] = None
    for boundary in boundaries:
        if boundary <= start_line:
            continue
        if boundary > max_end:
            break
        fallback = boundary
        if boundary not in avoid_boundaries:
            preferred = boundary
    return preferred if preferred is not None else fallback
