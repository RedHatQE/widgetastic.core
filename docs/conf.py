# -*- coding: utf-8 -*-
import os
import pkg_resources

from datetime import datetime

__distribution = pkg_resources.get_distribution('widgetastic.core')

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('http://docs.python.org/2.7', None),
    'selenium': ('http://selenium-python.readthedocs.org/', None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = __distribution.project_name
copyright = u'2016-{}, Milan Falešník (Apache license 2)'.format(datetime.now().year)
author = u'Milan Falešník'


# The full version, including alpha/beta/rc tags.
release = __distribution.version
version = '.'.join(release.split('.')[:2])

exclude_patterns = []

pygments_style = 'sphinx'
todo_include_todos = False


html_theme = 'classic'
html_static_path = ['_static']

htmlhelp_basename = 'deprecatedoc'


def run_apidoc(_):
    from sphinx.apidoc import main as apidoc_main
    modules = ['src/widgetastic']
    for module in modules:
        cur_dir = os.path.abspath(os.path.dirname(__file__))
        output_path = os.path.join(cur_dir, module, 'doc')
        apidoc_main(['-e', '-f', '-o', output_path, '.', '--force'])


def setup(app):
    app.connect('builder-inited', run_apidoc)
