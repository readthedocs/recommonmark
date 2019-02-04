"""Docutils CommonMark parser"""

__version__ = '0.5.0'


def setup(app):
    """Initialize Sphinx extension."""
    return {'version': __version__, 'parallel_read_safe': True}
