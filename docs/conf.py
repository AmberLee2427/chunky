"""Sphinx configuration for chunky documentation."""

from __future__ import annotations

import importlib.metadata
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

project = "chunky"
copyright = f"{datetime.now():%Y}, Nancy Brain Contributors"

try:
    release = importlib.metadata.version("chunky")
except importlib.metadata.PackageNotFoundError:
    from chunky.__about__ import __version__ as release  # type: ignore[assignment]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

autosummary_generate = True
napoleon_google_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True

html_theme = os.environ.get("SPHINX_HTML_THEME", "furo")
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", "https://docs.python.org/3/objects.inv"),
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

templates_path = ["_templates"]

exclude_patterns: list[str] = ["_build", "Thumbs.db", ".DS_Store"]
