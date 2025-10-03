# Chunky

Chunky is a python package for intelligently chunking scientific and technical repositories.
It provides a modular pipeline that powers the Nancy Brain knowledge base and MCP services,
while remaining useful as a standalone library for retrieval systems that need deterministic,
metadata-rich chunks.

## Highlights

- Deterministic sliding-window fallback that keeps progress even on unknown file types.
- Registry-driven architecture so language-specific chunkers can be added without touching callers.
- Rich metadata (`chunk_id`, `line_start`, `line_end`, character spans) ready for downstream RAG and citation tooling.
- Language-aware chunkers for Python, Markdown, YAML/JSON config, plain text, Fortran, and (via Tree-sitter) C/C++/HTML/Bash.
- Batteries-included tooling: Hatchling builds, Ruff linting, pytest coverage, Sphinx docs, and automated releases to PyPI + Read the Docs.

## Quick Start

```python
from pathlib import Path

from chunky import ChunkPipeline, ChunkerConfig

pipeline = ChunkPipeline()
config = ChunkerConfig(lines_per_chunk=80, line_overlap=10)

chunks = pipeline.chunk_file(Path("path/to/file.py"), config=config)

for chunk in chunks[:2]:
    print(chunk.chunk_id, chunk.metadata["line_start"], chunk.metadata["line_end"])
```

See the [design notes](docs/design/SEMANTIC_CHUNKER.md) for the roadmap toward language-aware and embedding-driven chunkers.

Documentation lives on Read the Docs: <https://chunky.readthedocs.io>

## Built-in Chunkers

* `PythonSemanticChunker` — splits modules on top-level functions/classes and groups leftover module context.
* `MarkdownHeadingChunker` — emits chunks per heading while keeping the optional intro section.
* `JSONYamlChunker` — slices configs by top-level keys/items and falls back gracefully when parsing fails.
* `PlainTextChunker` — groups blank-line-separated paragraphs before falling back to sliding windows.
* `FortranChunker` — captures subroutine/function/program blocks.
* Tree-sitter chunkers (optional extra) for C/C++, HTML, Bash, and other structural languages.
* `SlidingWindowChunker` — deterministic line windows with overlap when no specialised handler is available.

## Installation

Install from PyPI:

```bash
pip install chunky-files
```

Or install from source using the `pyproject.toml` metadata:

```bash
# clone the repo (if you haven't already)
git clone https://github.com/AmberLee2427/chunky.git
cd chunky

# install the library
pip install .
```

For development and documentation builds, install the optional extras:

```bash
pip install -e ".[dev,docs]"
```

To enable Tree-sitter powered chunkers for C/C++/HTML/Bash (and other supported grammars), install:

```bash
pip install chunky-files[tree]
```

This extra pins `tree-sitter==0.20.1` alongside the bundled `tree-sitter-languages` so the shipped grammar binaries load correctly.

> `-e` performs an editable install so local changes reflect immediately.
> `.[dev,docs]` installs the tooling declared under the `dev` and `docs` extras in `pyproject.toml`.

## Tooling

* **Code style:** Ruff (`ruff check src tests` or `ruff check src tests --fix`)
* **Tests:** Pytest (`pytest --cov=chunky`)
* **Docs:** Sphinx + MyST + Furo (`sphinx-build -b html docs docs/_build/html`)
* **Packaging:** Hatchling build backend
* **Versioning:** bump-my-version (driven by tags and the release workflow)

## Workflows

* CI tests run on Linux, macOS, and Windows for Python 3.8 through 3.12.
* Pushing a tag that matches the form `vX.Y.Z` triggers the release workflow. It validates that the
  tag matches the version in `pyproject.toml`, builds the distribution, and publishes to PyPI using
  the `PYPI_API_TOKEN` secret.
* Read the Docs builds the documentation automatically for pushes to the default branch. Local
  builds use `sphinx-build -b html docs docs/_build/html`.

Release checklist:

1. Review and update `CHANGELOG.md`, keeping the `[Unreleased]` section accurate.
2. Run `bump-my-version bump <part>` to update version metadata and append a dated entry in the
   changelog.
3. Build distributions locally (`rm -rf dist && python -m build`) and verify metadata with
   `python -m twine check dist/*`.
4. Commit the changes and push to `main`.
5. Tag the commit (`git tag vX.Y.Z && git push origin vX.Y.Z`) to trigger the Release workflow.
6. Verify the PyPI publish job and Read the Docs build succeed.

## Contributing

* Know your audience: most contributors will be scientific coders. Write docs assuming limited
  familiarity with packaging internals.
* Use Ruff for style checks and keep numpy-style docstrings on all non-test functions.
* Target test coverage above 70% and ensure existing CI jobs pass before opening a PR.
* In pull requests, summarise code changes, testing/validation, doc updates, and provide a brief
  TL;DR when the description runs long.

## License

Chunky is released under the [MIT License](LICENSE).

## Glossary

| Term | Meaning |
| ---- | ------- |
| PR | GitHub pull request – a request to merge one branch or fork with another |
| Release | Publishing a tagged version of the project to PyPI |
| ChangeLog | A document describing changes between releases |
| PyPI | Python Package Index – where published distributions live |
| Ruff | A fast Python linter/formatter used for style enforcement |
| origin | The upstream GitHub repository |
| fork | A downstream copy of the origin repo used for contributing |
| master/main | The default branch |
| CI | Continuous Integration – automated checks that run on every push/PR |
| GitHub Workflows | GitHub’s automation runner configured via YAML files |
| `pyproject.toml` | Core metadata and build configuration for the package |
| bump-my-version | CLI used to bump version numbers consistently |
| Read the Docs | Hosted documentation service that builds from the repo |
