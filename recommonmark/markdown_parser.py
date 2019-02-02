"""Docutils Markdown parser"""

import pydash as _
from docutils import parsers, nodes
from markdown import markdown
from html.parser import HTMLParser

__all__ = ['MarkdownParser']

class MarkdownParser(parsers.Parser):

    """Docutils parser for Markdown"""

    supported = ('md', 'markdown')
    translate_section_name = None
    level = 0

    def __init__(self):
        self._level_to_elem = {}

    def parse(self, inputstring, document):
        self.document = document
        self.current_node = document
        self.setup_parse(inputstring, document)
        html = markdown(inputstring + '\n', extensions=[
            'extra',
            'abbr',
            'attr_list',
            'def_list',
            'fenced_code',
            'footnotes',
            'tables',
            'admonition',
            'codehilite',
            'meta',
            'nl2br',
            'sane_lists',
            'smarty',
            'toc',
            'wikilinks'
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
        section.append(title)
        self.current_node.append(section)
        self.current_node = section

    def depart_section(self, level):
        if (self.current_node.parent):
            self.current_node = self.current_node.parent

    def visit_document(self):
        pass

    def depart_document(self):
        pass

    def visit_p(self, attrs):
        paragraph = nodes.paragraph()
        self.current_node.append(paragraph)
        self.current_node = paragraph

    def depart_p(self):
        self.current_node = self.current_node.parent

    def visit_text(self, data):
        text = nodes.Text(data)
        if isinstance(self.current_node, nodes.section) and len(self.current_node.children) > 0:
            title = self.current_node.children[0]
            if isinstance(title, nodes.title):
                title.append(text)
                self.current_node = title
                return None
        elif isinstance(self.current_node, nodes.title) and len(self.current_node.children) > 0:
            reference = self.current_node.children[0]
            if isinstance(reference, nodes.reference):
                reference.append(text)
                self.current_node = reference
                return None
        self.current_node.append(text)
        self.current_node = text

    def depart_text(self):
        self.current_node = self.current_node.parent

    def visit_h1(self, attrs):
        self.visit_section(1, attrs)

    def depart_h1(self):
        pass

    def visit_h2(self, attrs):
        self.visit_section(2, attrs)

    def depart_h2(self):
        pass

    def visit_h3(self, attrs):
        self.visit_section(3, attrs)

    def depart_h3(self):
        pass

    def visit_h4(self, attrs):
        self.visit_section(4, attrs)

    def depart_h4(self):
        pass

    def visit_h5(self, attrs):
        self.visit_section(5, attrs)

    def depart_h5(self):
        pass

    def visit_h6(self, attrs):
        self.visit_section(6, attrs)

    def depart_h6(self):
        pass

    def visit_a(self, attrs):
        reference = nodes.reference()
        reference['refuri'] = _.find(attrs, lambda i: i[0] == 'href')[1]
        if isinstance(self.current_node, nodes.section) and len(self.current_node.children) > 0:
            title = self.current_node.children[0]
            if isinstance(title, nodes.title):
                title.append(reference)
                self.current_node = title
                return None
        self.current_node.append(reference)
        self.current_node = reference

    def depart_a(self):
        self.current_node = self.current_node.parent

    def visit_img(self, attrs):
        print(attrs)
        image = nodes.image()
        image['uri'] = _.find(attrs, lambda attr:attr[0]=='src')[1]
        self.current_node.append(image)
        self.current_node = image
        self.visit_text(_.find(attrs, lambda attr:attr[0]=='alt')[1])

    def depart_img(self):
        self.depart_text()
        self.current_node = self.current_node.parent

    def visit_ul(self, attrs):
        bullet_list = nodes.bullet_list()
        self.current_node.append(bullet_list)
        self.current_node = bullet_list

    def depart_ul(self):
        self.current_node = self.current_node.parent

    def visit_ol(self, attrs):
        enumerated_list = nodes.enumerated_list()
        self.current_node.append(enumerated_list)
        self.current_node = enumerated_list

    def depart_ol(self):
        self.current_node = self.current_node.parent

    def visit_li(self, attrs):
        list_item = nodes.list_item()
        self.current_node.append(list_item)
        self.current_node = list_item
        self.visit_p([])

    def depart_li(self):
        self.depart_p()
        self.current_node = self.current_node.parent

    def visit_table(self, attrs):
        table = nodes.table()
        self.current_node.append(table)
        self.current_node = table

    def depart_table(self):
        self.current_node = self.current_node.parent

    def visit_thead(self, attrs):
        thead = nodes.thead()
        self.current_node.append(thead)
        self.current_node = thead

    def depart_thead(self):
        self.current_node = self.current_node.parent

    def visit_tbody(self, attrs):
        tbody = nodes.tbody()
        self.current_node.append(tbody)
        self.current_node = tbody

    def depart_tbody(self):
        self.current_node = self.current_node.parent

    def visit_tr(self, attrs):
        row = nodes.row()
        self.current_node.append(row)
        self.current_node = row

    def depart_tr(self):
        self.current_node = self.current_node.parent

    def visit_th(self, attrs):
        entry = nodes.entry()
        self.current_node.append(entry)
        self.current_node = entry

    def depart_th(self):
        self.current_node = self.current_node.parent

    def visit_td(self, attrs):
        entry = nodes.entry()
        self.current_node.append(entry)
        self.current_node = entry

    def depart_td(self):
        self.current_node = self.current_node.parent

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

    def visit_blockquote(self, attrs):
        block_quote = nodes.block_quote()
        self.current_node.append(block_quote)
        self.current_node = block_quote

    def depart_blockquote(self):
        self.current_node = self.current_node.parent

    def visit_hr(self, attrs):
        transition = nodes.transition()
        self.current_node.append(transition)
        self.current_node = transition

    def depart_hr(self):
        self.current_node = self.current_node.parent

    def visit_br(self, attrs):
        text = nodes.Text('\n')
        self.current_node.append(text)
        self.current_node = text

    def depart_br(self):
        self.current_node = self.current_node.parent
