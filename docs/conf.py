from datetime import datetime

# -- Project information -----------------------------------------------------

project = "widgetastic.core"
copyright = f"2016-{datetime.now().year}, Milan Falešník (Apache license 2)"
author = "Milan Falešník"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("http://docs.python.org/3.12/", None),
    "playwright": ("https://playwright.dev/python/", None),
}

templates_path = ["_templates"]

master_doc = "index"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "nature"
