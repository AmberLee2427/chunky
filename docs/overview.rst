Overview
========

Chunky exposes a modular pipeline for converting heterogeneous project artefacts into
well-behaved text chunks. The pipeline is language-aware, pluggable, and ready for
Nancy Brain's MCP-backed retrieval workflows.

.. note::
   See ``design/CHUNKY_V2_SPEC.md`` and ``design/CHUNK_MERGE_SPEC.md`` for
   implemented v2/v2.1 behavior.
   ``design/SEMANTIC_CHUNKER.md`` is retained as an archival early design draft.

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
   config = ChunkerConfig(
       max_chars=1000,
       min_chunk_chars=80,  # forward-merge tiny chunks into successor chunks
       lines_per_chunk=40,
       line_overlap=5,
   )
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
* ``RSTChunker`` — detects reStructuredText heading sections and chunks by section boundaries.
* ``NotebookChunker`` — groups nb4llm notebook exports (`.nb.txt`) into markdown+code context chunks.
* Tree-sitter chunkers (optional extra) for C/C++/HTML/Bash when the `tree` extra is installed.
* ``SlidingWindowChunker`` — deterministic line windows with configurable overlap.

Chunk identifiers default to ``<doc_id>#chunk-0000``. Provide ``Document.metadata['doc_id']`` (or set
``ChunkerConfig.doc_id_key``) and adjust the suffix with ``ChunkerConfig.chunk_id_template`` to suit your
downstream needs.

Forward-merge behavior
----------------------

Set ``ChunkerConfig.min_chunk_chars`` to a positive integer to merge tiny chunks into
their successor chunk (or into the predecessor for trailing tiny chunks). This keeps
small but meaningful context (imports, decorators, short comments/docstrings) attached
to nearby semantic content.

Roadmap
-------

* Phase 1: infrastructure scaffolding and sliding-window baseline.
* Phase 2: language-specific chunkers (Python, Markdown, JSON/YAML, notebooks, RST).
* Phase 3: semantic/embedding-driven chunking.
* Phase 4: documentation, benchmarks, and Nancy Brain integration.
