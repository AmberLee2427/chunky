# Chunky

Chunky is a python package for intelligently chunking scientific and technical repositories.
It provides a modular pipeline that powers the Nancy Brain knowledge base and MCP services,
while remaining useful as a standalone library for retrieval systems that need deterministic,
metadata-rich chunks.

Documentation lives on Read the Docs: <https://chunky.readthedocs.io>

## Installation

Install from source using the `pyproject.toml` metadata:

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

> `-e` performs an editable install so local changes reflect immediately.
> `.[dev,docs]` installs the tooling declared under the `dev` and `docs` extras in
> `pyproject.toml`.

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
3. Commit the changes and push to `main`.
4. Tag the commit (`git tag vX.Y.Z && git push origin vX.Y.Z`) to trigger the Release workflow.
5. Verify the PyPI publish job and Read the Docs build succeed.

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
