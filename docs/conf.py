# -*- coding: utf-8 -*-
import pkg_resources
import six
__distribution = pkg_resources.get_distribution('widgetastic.core')

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('http://docs.python.org/2.7', None),
    'pytest': ('http://pytest.org/latest/', None),
    'selenium': ('http://selenium-python.readthedocs.org/', None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = __distribution.project_name
copyright = u'2016, Milan Falešník'
author = u'Milan Falešník'


# The full version, including alpha/beta/rc tags.
release = __distribution.version
version = '.'.join(release.split('.')[:2])

exclude_patterns = []

pygments_style = 'sphinx'
todo_include_todos = False


html_theme = 'haiku'
html_static_path = ['_static']

htmlhelp_basename = 'deprecatedoc'
