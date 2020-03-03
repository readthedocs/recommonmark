
# -*- coding: utf-8 -*-

from recommonmark.parser import CommonMarkParser

templates_path = ['_templates']
source_parsers = { '.md': CommonMarkParser }

extensions = [
    'sphinx.ext.mathjax',
]
mathjax_config = {
    'extensions': ['tex2jax.js'],
    'jax': ['input/TeX', 'output/HTML-CSS'],
}
master_doc = 'index'
project = u'sphinxproj'
copyright = u'2015, rtfd'
author = u'rtfd'
version = '0.1'
release = '0.1'
highlight_language = 'python'
language = None
exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos = False
html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'sphinxproj'


