"""Sliding window fallback chunker."""

from __future__ import annotations

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document
from ._common import (
    compute_line_boundaries,
    compute_line_length_prefix,
    finalize_chunks,
    make_chunk,
    resolve_doc_id,
    span_char_length,
)


class SlidingWindowChunker(Chunker):
    """Chunker that produces fixed-size line windows with optional overlap."""

    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        lines = document.content.splitlines()
        requested_window = config.clamp_lines(config.lines_per_chunk)
        doc_id = resolve_doc_id(document, config)

        if not lines:
            chunk = make_chunk(
                document=document,
                lines=[""],
                start_line=0,
                end_line=1,
                chunk_index=0,
                config=config,
                line_starts=[0],
                line_ends=[0],
                doc_id=doc_id,
                chunk_id_template=config.chunk_id_template,
            )
            chunk.metadata.update({"line_start": 0, "line_end": 0})
            finalize_chunks([chunk], doc_id)
            return [chunk]

        chunks: list[Chunk] = []
        line_count = len(lines)
        # Pre-compute character offsets once to avoid quadratic scans.
        line_starts, line_ends = compute_line_boundaries(lines)
        length_prefix = compute_line_length_prefix(lines)

        sample = lines[:20]
        if sample:
            avg_line_len = max(1, sum(len(line) for line in sample) // len(sample))
        else:  # pragma: no cover - guarded by empty-lines branch above
            avg_line_len = 1
        max_chars = max(1, config.max_chars)
        char_window = max(1, max_chars // avg_line_len)
        window = max(1, min(requested_window, char_window))
        overlap = config.clamp_overlap(config.line_overlap, window)

        start_line = 0
        chunk_index = 0

        while start_line < line_count:
            previous_start = start_line
            end_line = min(start_line + window, line_count)

            while (
                end_line - start_line > 1
                and span_char_length(length_prefix, start_line, end_line) > max_chars
            ):
                end_line -= 1

            chunks.append(
                make_chunk(
                    document=document,
                    lines=lines,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_index=chunk_index,
                    config=config,
                    line_starts=line_starts,
                    line_ends=line_ends,
                    doc_id=doc_id,
                    chunk_id_template=config.chunk_id_template,
                )
            )

            chunk_index += 1
            if config.max_chunks and chunk_index >= config.max_chunks:
                break

            if end_line >= line_count:
                break

            next_start = end_line - overlap
            if next_start <= previous_start:
                next_start = end_line
            start_line = next_start

        finalize_chunks(chunks, doc_id)
        return chunks
