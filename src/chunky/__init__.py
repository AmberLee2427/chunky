"""Chunky: semantic chunking utilities for heterogeneous repositories."""

from .__about__ import __version__
from .pipeline import ChunkPipeline
from .types import Chunk, ChunkerConfig, Document

__all__ = [
    "__version__",
    "ChunkPipeline",
    "Chunk",
    "ChunkerConfig",
    "Document",
]
