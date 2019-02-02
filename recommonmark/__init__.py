"""Docutils CommonMark parser"""

__version__ = '0.5.0'


def setup(app):
    """Initialize Sphinx extension."""
    import sphinx
    from .parser import CommonMarkParser, MarkdownParser

    Parser = CommonMarkParser
    recommonmark_config = {}
    if hasattr(app.config, 'recommonmark_config'):
        recommonmark_config = app.config.recommonmark_config

    if 'parser' in recommonmark_config:
        if recommonmark_config['parser'] == 'Markdown':
            Parser = CommonMarkParser
    if sphinx.version_info >= (1, 8):
        app.add_source_suffix('.md', 'markdown')
        app.add_source_parser(Parser)
    elif sphinx.version_info >= (1, 4):
        app.add_source_parser('.md', Parser)

    return {'version': __version__, 'parallel_read_safe': True}
