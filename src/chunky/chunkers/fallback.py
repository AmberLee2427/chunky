"""Sliding window fallback chunker."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..core import Chunker
from ..types import Chunk, ChunkerConfig, Document


class SlidingWindowChunker(Chunker):
    """Chunker that produces fixed-size line windows with optional overlap."""

    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        lines = document.content.splitlines()
        window = config.clamp_lines(config.lines_per_chunk)
        overlap = config.clamp_overlap(config.line_overlap, window)

        if not lines:
            chunk_id = self._build_chunk_id(document.path, 0)
            return [
                Chunk(
                    chunk_id=chunk_id,
                    text="",
                    source_document=document.path,
                    metadata=self._chunk_metadata(
                        chunk_index=0,
                        line_start=0,
                        line_end=0,
                        span_start=0,
                        span_end=0,
                        config=config,
                    ),
                )
            ]

        chunks: list[Chunk] = []
        line_count = len(lines)
        # Pre-compute character offsets once to avoid quadratic scans.
        line_starts: list[int] = []
        line_ends: list[int] = []
        cursor = 0
        for idx, line in enumerate(lines):
            if idx > 0:
                cursor += 1  # newline preceding this line
            line_starts.append(cursor)
            cursor += len(line)
            line_ends.append(cursor)

        start_line = 0
        chunk_index = 0

        while start_line < line_count:
            previous_start = start_line
            end_line = min(start_line + window, line_count)
            text = "\n".join(lines[start_line:end_line])
            chunk_id = self._build_chunk_id(document.path, chunk_index)
            metadata = self._chunk_metadata(
                chunk_index=chunk_index,
                line_start=start_line + 1,
                line_end=end_line,
                span_start=line_starts[start_line],
                span_end=line_ends[end_line - 1],
                config=config,
            )

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=text,
                    source_document=document.path,
                    metadata=metadata,
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

        return chunks

    @staticmethod
    def _build_chunk_id(path: Path, index: int) -> str:
        return f"{path}::chunk-{index}"

    @staticmethod
    def _chunk_metadata(
        chunk_index: int,
        line_start: int,
        line_end: int,
        span_start: int,
        span_end: int,
        config: ChunkerConfig,
    ) -> dict[str, int | str]:
        metadata: dict[str, int | str] = {
            "chunk_index": chunk_index,
            "line_start": line_start,
            "line_end": line_end,
            "span_start": span_start,
            "span_end": span_end,
        }
        if config.metadata:
            metadata.update(config.metadata)
        return metadata
