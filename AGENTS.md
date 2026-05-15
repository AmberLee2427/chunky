# Agents

## Cursor Cloud specific instructions

**Project type:** Pure Python library (`chunky-files`) — no web servers, databases, Docker, or external services required.

### Prerequisites

`python3-dev` must be installed (provides `Python.h`) for the `tree-sitter==0.20.1` C extension build. The VM update script handles `pip install -e ".[dev]"`, but if `tree-sitter` fails to compile, run `sudo apt-get install -y python3-dev` first.

### Key commands

All commands are run from the repository root (`/workspace`).

| Task | Command |
|------|---------|
| Install deps | `pip install -e ".[dev]"` |
| Lint | `ruff check src tests` |
| Lint (autofix) | `ruff check src tests --fix` |
| Tests | `pytest --cov=chunky` |
| Docs (local) | `pip install -e ".[docs]" && sphinx-build -b html docs docs/_build/html` |

See `README.md` for the full tooling and workflow reference.

### Notes

- The `Chunk` dataclass uses `text` (not `content`) for the chunk body. `Document` uses `content`.
- `~/.local/bin` must be on `PATH` for `pytest`, `ruff`, and other pip-installed scripts. If missing, run `export PATH="$HOME/.local/bin:$PATH"`.
- No services to start or stop — the library is self-contained. Tests run in < 1 second.
- Code style: numpy-style docstrings, Ruff lint rules `E/F/I/B`, line length 100.
