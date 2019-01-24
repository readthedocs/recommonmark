
# -*- coding: utf-8 -*-

from recommonmark.parser import CommonMarkParser
from recommonmark.transform import AutoStructify

templates_path = ['_templates']
source_suffix = '.md'
source_parsers = { '.md': CommonMarkParser }
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

from docutils.parsers.rst import Parser
from docutils.utils import new_document
def transform_atom_markdown_plantuml(autostructify, node):
    params = node['language'].strip().split()
    language = params.pop(0)
    directives = []
    directives_string = u""
    for param in params:
        key, value = param.replace('{', '').replace('}', '').split('=')
        key = key.strip()
        value = value.strip()
        directives.append(u"   :%s: %s" % (key, value))

    if len(directives) > 0:
        directives_string = u"\n".join(directives) + u"\n"

    content = u"\n".join([u'   ' + l for l in node.rawsource.split('\n')])
    parser = Parser()
    new_doc = new_document(None, autostructify.document.settings)
    # if sphinxcontrib-plantuml is installed:
    # newsource = u'.. note::\n' + directives_string + u'   \n' + content
    newsource = u'.. note::\n' + directives_string + u'   \n' + content
    parser.parse(newsource, new_doc)
    return new_doc.children[:]


def setup(app):
    app.add_config_value(
        'recommonmark_config',
        {
            'auto_code_block_transformers': {
                'plantuml': transform_atom_markdown_plantuml
            },
        },
        True
    )
    app.add_transform(AutoStructify)
