"""Docutils Markdown parser"""

from docutils import parsers, nodes
from html.parser import HTMLParser
from markdown import markdown
import pydash as _
import re

__all__ = ['MarkdownParser']

class MarkdownParser(parsers.Parser):

    """Docutils parser for Markdown"""

    depth = 0
    level = 0
    supported = ('md', 'markdown')
    translate_section_name = None

    def __init__(self):
        self._level_to_elem = {}

    def parse(self, inputstring, document):
        self.document = document
        self.current_node = document
        self.setup_parse(inputstring, document)
        html = markdown(inputstring + '\n', extensions=[
            'extra',
            'tables',
            'sane_lists',
            'toc',
        ])
        self.convert_html(html)
        self.finish_parse()

    def convert_html(self, html):
        html = html.replace('\n', '')
        class MyHTMLParser(HTMLParser):
            def handle_starttag(_, tag, attrs):
                fn_name = 'visit_' + tag
                fn = getattr(self, fn_name)
                fn(attrs)
            def handle_endtag(_, tag):
                fn_name = 'depart_' + tag
                fn = getattr(self, fn_name)
                fn()
            def handle_data(_, data):
                self.visit_text(data)
                self.depart_text()
        self.visit_document()
        parser = MyHTMLParser()
        parser.feed(html)
        self.depart_document()

    def convert_ast(self, ast):
        for (node, entering) in ast.walker():
            fn_prefix = "visit" if entering else "depart"
            fn_name = "{0}_{1}".format(fn_prefix, node.t.lower())
            fn_default = "default_{0}".format(fn_prefix)
            fn = getattr(self, fn_name, None)
            if fn is None:
                fn = getattr(self, fn_default)
            fn(node)

    def visit_section(self, level, attrs):
        for i in range(self.level - level + 1):
            self.depart_section(level)
        self.level = level
        section = nodes.section()
        id_attr = _.find(attrs, lambda attr:attr[0]=='id')[1]
        section['ids'] = id_attr
        section['names'] = id_attr
        title = nodes.title()
        self.title_node = title
        section.append(title)
        self.append_node(section)

    def depart_section(self, level):
        if (self.current_node.parent):
            self.exit_node()

    def visit_document(self):
        pass

    def depart_document(self):
        pass

    def visit_p(self, attrs):
        paragraph = nodes.paragraph()
        self.append_node(paragraph)

    def depart_p(self):
        self.exit_node()

    def visit_text(self, data):
        text = nodes.Text(data)
        if self.title_node:
            self.title_node.append(text)
            self.title_node = text
        else:
            self.append_node(text)

    def depart_text(self):
        if self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def visit_h1(self, attrs):
        self.visit_section(1, attrs)

    def depart_h1(self):
        self.title_node = None

    def visit_h2(self, attrs):
        self.visit_section(2, attrs)

    def depart_h2(self):
        self.title_node = None

    def visit_h3(self, attrs):
        self.visit_section(3, attrs)

    def depart_h3(self):
        self.title_node = None

    def visit_h4(self, attrs):
        self.visit_section(4, attrs)

    def depart_h4(self):
        self.title_node = None

    def visit_h5(self, attrs):
        self.visit_section(5, attrs)

    def depart_h5(self):
        self.title_node = None

    def visit_h6(self, attrs):
        self.visit_section(6, attrs)

    def depart_h6(self):
        self.title_node = None

    def visit_a(self, attrs):
        reference = nodes.reference()
        reference['refuri'] = _.find(attrs, lambda i: i[0] == 'href')[1]
        if self.title_node:
            self.title_node.append(reference)
            self.title_node = reference
        else:
            self.append_node(reference)

    def depart_a(self):
        if self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def visit_img(self, attrs):
        image = nodes.image()
        image['uri'] = _.find(attrs, lambda attr:attr[0]=='src')[1]
        self.append_node(image)
        self.visit_text(_.find(attrs, lambda attr:attr[0]=='alt')[1])

    def depart_img(self):
        self.depart_text()
        self.exit_node()

    def visit_ul(self, attrs):
        bullet_list = nodes.bullet_list()
        self.append_node(bullet_list)

    def depart_ul(self):
        self.exit_node()

    def visit_ol(self, attrs):
        enumerated_list = nodes.enumerated_list()
        self.append_node(enumerated_list)

    def depart_ol(self):
        self.exit_node()

    def visit_li(self, attrs):
        list_item = nodes.list_item()
        self.append_node(list_item)
        self.visit_p([])

    def depart_li(self):
        self.depart_p()
        self.exit_node()

    def visit_table(self, attrs):
        table = nodes.table()
        self.append_node(table)

    def depart_table(self):
        self.exit_node()

    def visit_thead(self, attrs):
        thead = nodes.thead()
        self.append_node(thead)

    def depart_thead(self):
        self.exit_node()

    def visit_tbody(self, attrs):
        tbody = nodes.tbody()
        self.append_node(tbody)

    def depart_tbody(self):
        self.exit_node()

    def visit_tr(self, attrs):
        row = nodes.row()
        self.append_node(row)

    def depart_tr(self):
        self.exit_node()

    def visit_th(self, attrs):
        entry = nodes.entry()
        self.append_node(entry)

    def depart_th(self):
        self.exit_node()

    def visit_td(self, attrs):
        entry = nodes.entry()
        self.append_node(entry)

    def depart_td(self):
        self.exit_node()

    def visit_div(self, attrs):
        pass

    def depart_div(self):
        pass

    def visit_pre(self, attrs):
        pass

    def depart_pre(self):
        pass

    def visit_span(self, attrs):
        pass

    def depart_span(self):
        pass

    def visit_code(self, attrs):
        literal_block = nodes.literal_block()
        attr = _.find(attrs, lambda attr:attr[0]=='class')
        if len(attr):
            class_attr = attr[1]
            literal_block['language'] = class_attr
        self.append_node(literal_block)

    def depart_code(self):
        self.exit_node()

    def visit_blockquote(self, attrs):
        block_quote = nodes.block_quote()
        self.append_node(block_quote)

    def depart_blockquote(self):
        self.exit_node()

    def visit_hr(self, attrs):
        transition = nodes.transition()
        self.append_node(transition)

    def depart_hr(self):
        self.exit_node()

    def visit_br(self, attrs):
        text = nodes.Text('\n')
        self.append_node(text)

    def depart_br(self):
        self.exit_node()

    def visit_em(self, attrs):
        emphasis = nodes.emphasis()
        if self.title_node:
            self.title_node.append(emphasis)
            self.title_node = emphasis
        else:
            self.append_node(emphasis)

    def depart_em(self):
        if self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def visit_strong(self, attrs):
        strong = nodes.strong()
        if self.title_node:
            self.title_node.append(strong)
            self.title_node = strong
        else:
            self.append_node(strong)

    def depart_strong(self):
        if self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def append_node(self, node):
        self.current_node.append(node)
        self.current_node = node
        self.depth = self.depth + 1

    def exit_node(self):
        self.current_node = self.current_node.parent
        self.depth = self.depth - 1
