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

Install the package from PyPI or from source:

.. code-block:: bash

   pip install chunky-files

.. code-block:: bash
   :caption: from source

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

Built-in chunkers
------------------

* ``PythonSemanticChunker`` — splits modules on top-level functions/classes and captures remaining context.
* ``MarkdownHeadingChunker`` — groups content per heading while keeping introductory prose.
* ``JSONYamlChunker`` — slices structured configs by their first-level keys/items and falls back if parsing fails.
* ``PlainTextChunker`` — groups blank-line separated paragraphs before falling back to sliding windows.
* ``FortranChunker`` — captures `program`, `subroutine`, and `function` blocks with minimal heuristics.
* Tree-sitter chunkers (optional extra) for C/C++/HTML/Bash when the `tree` extra is installed.
* ``SlidingWindowChunker`` — deterministic line windows with configurable overlap.

Roadmap
-------

* Phase 1: infrastructure scaffolding and sliding-window baseline.
* Phase 2: language-specific chunkers (Python, Markdown, JSON/YAML, notebooks).
* Phase 3: semantic/embedding-driven chunking.
* Phase 4: documentation, benchmarks, and Nancy Brain integration.
