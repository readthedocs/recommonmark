# recommonmark

A `docutils`-compatibility bridge to [CommonMark][cm].

This allows you to write CommonMark inside of Docutils & Sphinx projects.

Documentation is available on Read the Docs: <http://recommonmark.readthedocs.org>

Contents
--------
* [API Reference](api_ref.md)
* [AutoStructify Component](auto_structify.md)

## Getting Started

To use `recommonmark` inside of Sphinx only takes 2 steps. 
First you install it:

```
pip install recommonmark 
```

Then add this to your Sphinx conf.py:

```
from recommonmark.parser import CommonMarkParser

source_parsers = {'.md': CommonMarkParser}

source_suffix = ['.rst', '.md']
```

This allows you to write both `.md` and `.rst` files inside of the same project.

## Development

You can run the tests by running `tox` in the top-level of the project.

We are working to expand test coverage,
but this will at least test basic Python 2 and 3 compatability.

## Why a bridge?

Many python tools (mostly for documentation creation) rely on `docutils`.
But [docutils][dc] only supports a ReStructuredText syntax.

For instance [this issue][sphinx-issue] and [this StackOverflow
question][so-question] show that there is an interest in allowing `docutils`
to use markdown as an alternative syntax.

## Why another bridge to docutils?

recommonmark uses the [python implementation][pcm] of [CommonMark][cm] while
[remarkdown][rmd] implements a stand-alone parser leveraging [parsley][prs].

Both output a [`docutils` document tree][dc] and provide scripts
that leverage `docutils` for generation of different types of documents.

## Acknowledgement

recommonmark is mainly derived from [remarkdown][rmd] by Steve Genoud and
leverages the python CommonMark implementation.

It was originally created by [Luca Barbato][lu-zero],
and is now maintained in the Read the Docs (rtfd) GitHub organization.

[cm]: http://commonmark.org
[pcm]: https://github.com/rolandshoemaker/CommonMark-py
[rmd]: https://github.com/sgenoud/remarkdown
[prs]: https://github.com/python-parsley/parsley
[lu-zero]: https://github.com/lu-zero

[dc]: http://docutils.sourceforge.net/docs/ref/doctree.html
[sphinx-issue]: https://bitbucket.org/birkenfeld/sphinx/issue/825/markdown-capable-sphinx
[so-question]: http://stackoverflow.com/questions/2471804/using-sphinx-with-markdown-instead-of-rst
