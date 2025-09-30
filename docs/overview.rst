Overview
========

Chunky exposes a modular pipeline for converting heterogeneous project artefacts into
well-behaved text chunks. The pipeline is language-aware, pluggable, and ready for
Nancy Brain's MCP-backed retrieval workflows.

.. note::
   The implementation is in active development. See ``SEMANTIC_CHUNKER.md`` for the full
   design document and roadmap.

Getting Started
---------------

Install the package from source:

.. code-block:: bash

   git clone https://github.com/AmberLee2427/chunky.git
   cd chunky
   pip install .

For development work and documentation builds:

.. code-block:: bash

   pip install -e ".[dev,docs]"

First chunks via the pipeline:

.. code-block:: python

   from pathlib import Path

   from chunky import ChunkPipeline, ChunkerConfig

   pipeline = ChunkPipeline()
   config = ChunkerConfig(lines_per_chunk=80, line_overlap=10)
   chunks = pipeline.chunk_file(Path("/path/to/file.py"), config=config)

   for chunk in chunks:
       print(chunk.chunk_id, chunk.metadata["line_start"], chunk.metadata["line_end"])

Roadmap
-------

* Phase 1: infrastructure scaffolding and sliding-window baseline.
* Phase 2: language-specific chunkers (Python, Markdown, JSON/YAML, notebooks).
* Phase 3: semantic/embedding-driven chunking.
* Phase 4: documentation, benchmarks, and Nancy Brain integration.
