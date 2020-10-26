from datetime import datetime

# -- Project information -----------------------------------------------------

project = 'widgetastic.core'
copyright = '2016-{}, Milan Falešník (Apache license 2)'.format(datetime.now().year)
author = 'Milan Falešník'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('http://docs.python.org/3.8/', None),
    'selenium': ('http://selenium-python.readthedocs.org/', None),
}

templates_path = ['_templates']

master_doc = 'index'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

html_theme = 'nature'
