"""Docutils Markdown parser"""

from docutils import parsers, nodes
from html.parser import HTMLParser
from markdown import markdown
from pydash import _
import re

__all__ = ['MarkdownParser']

class MarkdownParser(parsers.Parser):

    """Docutils parser for Markdown"""

    depth = 0
    html_mode = False
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
                attrs = self.attrs_to_dict(attrs)
                fn_name = 'visit_' + tag
                if hasattr(self, fn_name):
                    fn = getattr(self, fn_name)
                    fn(attrs)
                else:
                    self.visit_html(tag, attrs)
            def handle_endtag(_, tag):
                fn_name = 'depart_' + tag
                if hasattr(self, fn_name):
                    fn = getattr(self, fn_name)
                    fn()
                else:
                    self.depart_html(tag)
            def handle_data(_, data):
                self.visit_text(data)
                self.depart_text()
        self.visit_document()
        parser = MyHTMLParser()
        parser.feed(html)
        self.depart_document()

    def attrs_to_dict(self, attrs):
        attrs_dict = {}
        for item in attrs:
            if len(item) == 2:
                attrs_dict[item[0]] = item[1]
        return attrs_dict

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
        id_attr = attrs['id'] if 'id' in attrs else ''
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
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('p', attrs)
        else:
            paragraph = nodes.paragraph()
            self.append_node(paragraph)

    def depart_p(self):
        if self.html_mode:
            self.depart_html('p', attrs)
        else:
            self.exit_node()

    def visit_text(self, data):
        text = nodes.Text(data)
        if self.html_mode:
            text = nodes.Text(self.current_node.children[0].astext() + data)
            self.current_node.children[0] = text
        elif self.title_node:
            self.title_node.append(text)
            self.title_node = text
        else:
            self.append_node(text)

    def depart_text(self):
        if self.html_mode:
            pass
        elif self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def visit_h1(self, attrs):
        if self.html_mode or _.keys(attrs) != ['id']:
            self.visit_html('h1', attrs)
        else:
            self.visit_section(1, attrs)

    def depart_h1(self):
        if self.html_mode:
            self.depart_html('h1')
        else:
            self.title_node = None

    def visit_h2(self, attrs):
        if self.html_mode or _.keys(attrs) != ['id']:
            self.visit_html('h2', attrs)
        else:
            self.visit_section(2, attrs)

    def depart_h2(self):
        if self.html_mode:
            self.depart_html('h2')
        else:
            self.title_node = None

    def visit_h3(self, attrs):
        if self.html_mode or _.keys(attrs) != ['id']:
            self.visit_html('h3', attrs)
        else:
            self.visit_section(3, attrs)

    def depart_h3(self):
        if self.html_mode:
            self.depart_html('h3')
        else:
            self.title_node = None

    def visit_h4(self, attrs):
        if self.html_mode or _.keys(attrs) != ['id']:
            self.visit_html('h4', attrs)
        else:
            self.visit_section(4, attrs)

    def depart_h4(self):
        if self.html_mode:
            self.depart_html('h4')
        else:
            self.title_node = None

    def visit_h5(self, attrs):
        if self.html_mode or _.keys(attrs) != ['id']:
            self.visit_html('h5', attrs)
        else:
            self.visit_section(5, attrs)

    def depart_h5(self):
        if self.html_mode:
            self.depart_html('h5')
        else:
            self.title_node = None

    def visit_h6(self, attrs):
        if self.html_mode or _.keys(attrs) != ['id']:
            self.visit_html('h6', attrs)
        else:
            self.visit_section(6, attrs)

    def depart_h6(self):
        if self.html_mode:
            self.depart_html('h6')
        else:
            self.title_node = None

    def visit_a(self, attrs):
        if self.html_mode or _.keys(attrs) != ['href']:
            self.visit_html('a', attrs)
        else:
            reference = nodes.reference()
            reference['refuri'] = attrs['href'] if 'href' in attrs else ''
            if self.title_node:
                self.title_node.append(reference)
                self.title_node = reference
            else:
                self.append_node(reference)

    def depart_a(self):
        if self.html_mode:
            self.depart_html('a')
        elif self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def visit_img(self, attrs):
        if self.html_mode or _.keys(attrs) != ['alt', 'src']:
            self.visit_html('img', attrs)
        else:
            image = nodes.image()
            image['uri'] = attrs['src'] if 'src' in attrs else ''
            self.append_node(image)
            self.visit_text(attrs['alt'] if 'alt' in attrs else '')

    def depart_img(self):
        if self.html_mode:
            self.depart_html('img')
        else:
            self.depart_text()
            self.exit_node()

    def visit_ul(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('ul', attrs)
        else:
            bullet_list = nodes.bullet_list()
            self.append_node(bullet_list)

    def depart_ul(self):
        if self.html_mode:
            self.depart_html('ul')
        else:
            self.exit_node()

    def visit_ol(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('ol', attrs)
        else:
            enumerated_list = nodes.enumerated_list()
            self.append_node(enumerated_list)

    def depart_ol(self):
        if self.html_mode:
            self.depart_html('ol')
        else:
            self.exit_node()

    def visit_li(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('li', attrs)
        else:
            list_item = nodes.list_item()
            self.append_node(list_item)
            self.visit_p([])

    def depart_li(self):
        if self.html_mode:
            self.depart_html('li')
        else:
            self.depart_p()
            self.exit_node()

    def visit_table(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('table', attrs)
        else:
            table = nodes.table()
            self.append_node(table)

    def depart_table(self):
        if self.html_mode:
            self.depart_html('table')
        else:
            self.exit_node()

    def visit_thead(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('thead', attrs)
        else:
            thead = nodes.thead()
            self.append_node(thead)

    def depart_thead(self):
        if self.html_mode:
            self.depart_html('thead')
        else:
            self.exit_node()

    def visit_tbody(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('tbody', attrs)
        else:
            tbody = nodes.tbody()
            self.append_node(tbody)

    def depart_tbody(self):
        if self.html_mode:
            self.html_mode('tbody')
        else:
            self.exit_node()

    def visit_tr(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('tr', attrs)
        else:
            row = nodes.row()
            self.append_node(row)

    def depart_tr(self):
        if self.html_mode:
            self.depart_html('tr')
        else:
            self.exit_node()

    def visit_th(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('th', attrs)
        else:
            entry = nodes.entry()
            self.append_node(entry)

    def depart_th(self):
        if self.html_mode:
            self.depart_html('th')
        else:
            self.exit_node()

    def visit_td(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('td', attrs)
        else:
            entry = nodes.entry()
            self.append_node(entry)

    def depart_td(self):
        if self.html_mode:
            self.depart_html('td')
        else:
            self.exit_node()

    def visit_pre(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('pre', attrs)

    def depart_pre(self):
        if self.html_mode:
            self.depart_html('pre')

    def visit_code(self, attrs):
        if self.html_mode or _.keys(attrs) != ['class']:
            self.visit_html('code', attrs)
        else:
            literal_block = nodes.literal_block()
            class_attr = attrs['class'] if 'class' in attrs else ''
            if len(class_attr):
                literal_block['language'] = class_attr
            self.append_node(literal_block)

    def depart_code(self):
        if self.html_mode:
            self.depart_html('code')
        else:
            self.exit_node()

    def visit_blockquote(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('blockquote', attrs)
        else:
            block_quote = nodes.block_quote()
            self.append_node(block_quote)

    def depart_blockquote(self):
        if self.html_mode:
            self.depart_html('blockquote')
        else:
            self.exit_node()

    def visit_hr(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('hr', attrs)
        else:
            transition = nodes.transition()
            self.append_node(transition)

    def depart_hr(self):
        if self.html_mode:
            self.depart_html('hr')
        else:
            self.exit_node()

    def visit_br(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('br', attrs)
        else:
            text = nodes.Text('\n')
            self.append_node(text)

    def depart_br(self):
        if self.html_mode:
            self.depart_html('br')
        else:
            self.exit_node()

    def visit_em(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('em', attrs)
        else:
            emphasis = nodes.emphasis()
            if self.title_node:
                self.title_node.append(emphasis)
                self.title_node = emphasis
            else:
                self.append_node(emphasis)

    def depart_em(self):
        if self.html_mode:
            self.depart_html('em')
        elif self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def visit_strong(self, attrs):
        if self.html_mode or len(_.keys(attrs)):
            self.visit_html('strong', attrs)
        else:
            strong = nodes.strong()
            if self.title_node:
                self.title_node.append(strong)
                self.title_node = strong
            else:
                self.append_node(strong)

    def depart_strong(self):
        if self.html_mode:
            self.depart_html('strong')
        elif self.title_node:
            self.title_node = self.title_node.parent
        else:
            self.exit_node()

    def visit_html(self, tag, attrs):
        if not self.html_mode:
            raw = nodes.raw()
            raw['format'] = 'html'
            self.current_node.append(raw)
            self.current_node = raw
            self.html_mode = self.depth + 1
        tag_html = '<' + tag + ''.join(
            _.map(attrs, lambda value, attr: ' ' + attr + '="' + value + '"')
        ) + '>'
        if len(self.current_node.children):
            text = nodes.Text(
                self.current_node.children[0].astext() + tag_html
            )
            self.current_node.children[0] = text
        else:
            text = nodes.Text(tag_html)
            self.current_node.append(text)
        self.depth = self.depth + 1

    def depart_html(self, tag):
        text = nodes.Text(self.current_node.children[0].astext() + '</' + tag + '>')
        self.current_node.children[0] = text
        if self.depth == self.html_mode:
            self.current_node = self.current_node.parent
            self.html_mode = False
        self.depth = self.depth - 1

    def append_node(self, node):
        self.current_node.append(node)
        self.current_node = node
        self.depth = self.depth + 1

    def exit_node(self):
        self.current_node = self.current_node.parent
        self.depth = self.depth - 1
