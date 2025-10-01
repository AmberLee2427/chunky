# Bug Report: PyPI Publish Workflow Metadata Error

## Summary

The GitHub Actions workflow for publishing the `chunky-files` package to PyPI fails with the error:

```
ERROR   InvalidDistribution: Metadata is missing required fields: Name, Version.
```

This bug report documents all the things that have been ruled out as causes for this error.

---

## What This Is NOT

### 1. Not a PyPI Token or Authentication Issue
- The `PYPI_TOKEN` is correctly set as a GitHub Actions secret and referenced in the workflow.
- The workflow reaches the publish step and attempts to upload, indicating authentication is working.

### 2. Not a Local Build Problem
- Local builds using `python -m build` produce valid wheel and sdist files.
- The `twine check dist/*` command passes for both wheel and sdist.
- The wheel contains a valid `METADATA` file with `Name` and `Version` fields.
- Local inspection with `python -m zipfile -l dist/*.whl` confirms the presence of metadata files.
- Upload succeeds (version was bumped after sucessful local upload to avoid conflicts with future workflow runs).

### 3. Not a Project Metadata Issue
- The `pyproject.toml` contains the correct `[project]` section with `name = "chunky-files"` and a valid `version`.
- The project builds and installs locally without errors.

### 4. Not a Workflow Cleanliness Issue
- The workflow includes steps to remove the `dist/` directory before building.
- The build step uses `python -m build` from the project root.
- The workflow lists the contents of the `dist/` directory, confirming only the expected files are present.

### 5. Not a Package Naming or Import Issue
- The package directory is `chunky/`, but the project name is `chunky-files` as required for PyPI.
- The wheel and sdist are named correctly and contain the expected files.

### 6. Not a Version Mismatch
- The workflow checks that the git tag matches the project version in `pyproject.toml`.

### 7. Not a Problem With Build Tools
- The workflow installs and upgrades `pip`, `build`, and `hatchling` before building.
- No errors are reported during the build process.

### 8. Not a Problem With Twine or Metadata Verification
- The workflow can run `twine check dist/*` and it passes.

---

## Remaining Suspicions
- The error may be caused by a bug or regression in the `pypa/gh-action-pypi-publish` action itself.
- The error message is actively unhelpful and metadata is not the issue.

---

## Next Steps
- Try downgrading the `pypa/gh-action-pypi-publish` action to a previous version (e.g., v1.8.10).
- Add a step to remove both `build/` directories before building.
- Add a `twine check` step in the workflow before publish.
- If the error persists, report the issue to the maintainers of `pypa/gh-action-pypi-publish` with this bug report.

---

## References
- [PyPI Help: API Tokens](https://pypi.org/help/#apitoken)
- [PyPI Name Claim Process](https://pypi.org/help/#claiming-a-name)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
