# -*- coding: utf-8 -*-

import unittest
from textwrap import dedent

from docutils import nodes
from docutils.utils import new_document
from docutils.readers import Reader
from docutils.core import publish_parts

from commonmark import Parser
from recommonmark.parser import MarkdownParser, CommonMarkParser

class TestParsing(unittest.TestCase):

    def assertParses(self, source, expected, alt=False):  # noqa
        parser = MarkdownParser()
        parser.parse(dedent(source), new_document('<string>'))
        self.assertMultiLineEqual(
            dedent(expected).lstrip(),
            dedent(parser.document.asdom().toprettyxml(indent='  ')),
        )

    def test_heading(self):
        self.assertParses(
            """
            # I

            ```py
            hello = 'world'
            ```

            ## A

            > some-blockquote

            [google](https://www.google.com)

            ## [B](#b)

            ![ello](some-image.img)

            * one
            * two

            1. ONE
            2. TWO

            _italicize_

            **bold**

            ---

            | one | two |
            | --- | --- |
            | ONE | TWO |
            """,
            """
            <?xml version="1.0" ?>
            <document source="&lt;string&gt;">
              <section ids="i" names="i">
                <title>I</title>
                <literal_block language="py" xml:space="preserve">hello = 'world'</literal_block>
                <section ids="a" names="a">
                  <title>A</title>
                  <block_quote>
                    <paragraph>some-blockquote</paragraph>
                  </block_quote>
                  <paragraph>
                    <reference refuri="https://www.google.com">google</reference>
                  </paragraph>
                </section>
                <section ids="b" names="b">
                  <title>
                    <reference refuri="#b">B</reference>
                  </title>
                  <paragraph>
                    <image uri="some-image.img">ello</image>
                  </paragraph>
                  <bullet_list>
                    <list_item>
                      <paragraph>one</paragraph>
                    </list_item>
                    <list_item>
                      <paragraph>two</paragraph>
                    </list_item>
                  </bullet_list>
                  <enumerated_list>
                    <list_item>
                      <paragraph>ONE</paragraph>
                    </list_item>
                    <list_item>
                      <paragraph>TWO</paragraph>
                    </list_item>
                  </enumerated_list>
                  <paragraph>
                    <emphasis>italicize</emphasis>
                  </paragraph>
                  <paragraph>
                    <strong>bold</strong>
                  </paragraph>
                  <transition/>
                  <table>
                    <thead>
                      <row>
                        <entry>one</entry>
                        <entry>two</entry>
                      </row>
                    </thead>
                    <tbody>
                      <row>
                        <entry>ONE</entry>
                        <entry>TWO</entry>
                      </row>
                    </tbody>
                  </table>
                </section>
              </section>
            </document>
            """
        )

if __name__ == '__main__':
    unittest.main()
