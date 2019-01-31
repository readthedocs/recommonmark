# -*- coding: utf-8 -*-

import unittest
from textwrap import dedent

from docutils import nodes
from docutils.utils import new_document
from docutils.readers import Reader
from docutils.core import publish_parts

from commonmark import Parser
from recommonmark.parser import CommonMarkParser


class TestParsing(unittest.TestCase):

    def assertParses(self, source, expected, alt=False):  # noqa
        parser = CommonMarkParser()
        parser.parse(dedent(source), new_document('<string>'))
        self.assertMultiLineEqual(
            dedent(expected).lstrip(),
            dedent(parser.document.asdom().toprettyxml(indent='  ')),
        )

    def test_heading(self):
        self.assertParses(
            """
            ---
            ___

            # h1

            ## h2


            [Google](https://google.com)

            ## h22

            one
            two

            three
            four

            """,
            """
            <?xml version="1.0" ?>
            <document source="&lt;string&gt;">
              <paragraph>hi</paragraph>
            </document>
            """
        )

if __name__ == '__main__':
    unittest.main()
