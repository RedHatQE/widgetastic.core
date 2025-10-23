# Configuration file for the Sphinx documentation builder.
import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------

sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------

project = "Widgetastic.Core"
author = "Milan Falešník, Red Hat, Inc."
copyright = (
    f"2016-2019, Milan Falešník; 2020-{datetime.now().year}, Red Hat, Inc. (Apache license 2)"
)

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
]

master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

# -- Extension configuration -------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    # Playwright doesn't have a proper intersphinx inventory yet
    # "playwright": ("https://playwright.dev/python/", None),
}

# Configure warnings and error handling
nitpick_ignore = [
    # Ignore missing references that are known to be problematic
    ("py:class", "RootResolverError"),  # anytree reference that may not exist
    ("py:exc", "RootResolverError"),  # Exception variant
    ("any", "RootResolverError"),  # Any reference type
]

autodoc_member_order = "bysource"
autosummary_generate = True

# Suppress warnings for missing references
suppress_warnings = ["ref.python"]

# Make cross-references non-strict to avoid ambiguity errors
nitpicky = False

# Configure autodoc to be less strict about signatures and types
autodoc_typehints = "description"
autodoc_type_aliases = {}

# Configure autosummary
autosummary_mock_imports = []

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
