"""Sphinx configuration for Fast FSM documentation."""

import sys
from pathlib import Path

# -- Path setup --------------------------------------------------------
# Add src/ so autodoc can import fast_fsm
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# -- Project information -----------------------------------------------
project = "Fast FSM"
copyright = "2026, Fast FSM Contributors"
author = "Fast FSM Contributors"
release = "0.1.0"

# -- General configuration ---------------------------------------------
extensions = [
    # Constitution-mandated stack (§ Quality Gates > Documentation)
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    # Markdown support — keeps existing .md docs working as-is
    "myst_parser",
]

# File types Sphinx should process
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The root toctree document
root_doc = "index"

# Patterns to exclude from source discovery
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

# -- MyST (Markdown) settings ------------------------------------------
myst_enable_extensions = [
    "colon_fence",       # ::: directives in markdown
    "fieldlist",         # :field: syntax
    "deflist",           # definition lists
    "tasklist",          # - [x] checkboxes
]
myst_heading_anchors = 3  # auto-generate anchors for h1-h3

# Suppress warnings for cross-references to files outside the docs tree
# (README.md, examples/, src/ etc. are valid in-repo links but not Sphinx docs)
suppress_warnings = ["myst.xref_missing"]

# -- Napoleon settings (Google-style docstrings) -----------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# -- Autodoc settings --------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"  # types in description, not signature
autodoc_class_signature = "separated"

# -- sphinx-autodoc-typehints settings ---------------------------------
always_document_param_types = True
typehints_defaults = "comma"

# -- Intersphinx -------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- HTML output -------------------------------------------------------
html_theme = "furo"
html_title = "Fast FSM"
html_static_path = ["_static"]

# Furo theme options
html_theme_options = {
    "source_repository": "",
    "source_branch": "main",
    "source_directory": "docs/",
}
