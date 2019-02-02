"""Docutils CommonMark parser"""

import sys
from os.path import splitext

import pydash as _

from docutils import parsers, nodes
from sphinx import addnodes

from commonmark import Parser

from warnings import warn

from markdown import markdown
from html.parser import HTMLParser

if sys.version_info < (3, 0):
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

__all__ = ['CommonMarkParser']


class CommonMarkParser(parsers.Parser):

    """Docutils parser for CommonMark"""

    supported = ('md', 'markdown')
    translate_section_name = None
    level = 0

    def __init__(self):
        self._level_to_elem = {}

    def parse(self, inputstring, document):
        self.document = document
        self.current_node = document
        self.setup_parse(inputstring, document)
        self.setup_sections()
        parser = Parser()
        ast = parser.parse(inputstring + '\n')
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
        print(html)
        self.convert_html(html)
        # self.convert_ast(ast)
        self.finish_parse()
        print('----------------------')
        print(self.document)

    def convert_html(self, html):
        html = html.replace('\n', '')
        class MyHTMLParser(HTMLParser):
            def handle_starttag(_, tag, attrs):
                fn_name = '_visit_' + tag
                fn = getattr(self, fn_name)
                fn(attrs)
            def handle_endtag(_, tag):
                fn_name = '_depart_' + tag
                fn = getattr(self, fn_name)
                fn()
            def handle_data(_, data):
                self._visit_text(data)
                self._depart_text()
        self._visit_document()
        parser = MyHTMLParser()
        parser.feed(html)
        self._depart_document()

    def convert_ast(self, ast):
        for (node, entering) in ast.walker():
            fn_prefix = "visit" if entering else "depart"
            fn_name = "{0}_{1}".format(fn_prefix, node.t.lower())
            fn_default = "default_{0}".format(fn_prefix)
            fn = getattr(self, fn_name, None)
            if fn is None:
                fn = getattr(self, fn_default)
            fn(node)

    def _visit_section(self, level, attrs):
        for i in range(self.level - level + 1):
            self._depart_section(level)
        self.level = level
        section = nodes.section()
        id_attr = _.find(attrs, lambda attr:attr[0]=='id')[1]
        section['ids'] = id_attr
        section['names'] = id_attr
        title = nodes.title()
        section.append(title)
        self.current_node.append(section)
        self.current_node = section

    def _depart_section(self, level):
        if (self.current_node.parent):
            self.current_node = self.current_node.parent

    def _visit_document(self):
        pass

    def _depart_document(self):
        pass

    def _visit_p(self, attrs):
        paragraph = nodes.paragraph()
        self.current_node.append(paragraph)
        self.current_node = paragraph

    def _depart_p(self):
        self.current_node = self.current_node.parent

    def _visit_text(self, data):
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

    def _depart_text(self):
        self.current_node = self.current_node.parent

    def _visit_h1(self, attrs):
        self._visit_section(1, attrs)

    def _depart_h1(self):
        pass

    def _visit_h2(self, attrs):
        self._visit_section(2, attrs)

    def _depart_h2(self):
        pass

    def _visit_h3(self, attrs):
        self._visit_section(3, attrs)

    def _depart_h3(self):
        pass

    def _visit_h4(self, attrs):
        self._visit_section(4, attrs)

    def _depart_h4(self):
        pass

    def _visit_h5(self, attrs):
        self._visit_section(5, attrs)

    def _depart_h5(self):
        pass

    def _visit_h6(self, attrs):
        self._visit_section(6, attrs)

    def _depart_h6(self):
        pass

    def _visit_a(self, attrs):
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

    def _depart_a(self):
        self.current_node = self.current_node.parent

    def _visit_img(self, attrs):
        print(attrs)
        image = nodes.image()
        image['uri'] = _.find(attrs, lambda attr:attr[0]=='src')[1]
        self.current_node.append(image)
        self.current_node = image
        self._visit_text(_.find(attrs, lambda attr:attr[0]=='alt')[1])

    def _depart_img(self):
        self._depart_text()
        self.current_node = self.current_node.parent

    def _visit_ul(self, attrs):
        bullet_list = nodes.bullet_list()
        self.current_node.append(bullet_list)
        self.current_node = bullet_list

    def _depart_ul(self):
        self.current_node = self.current_node.parent

    def _visit_ol(self, attrs):
        enumerated_list = nodes.enumerated_list()
        self.current_node.append(enumerated_list)
        self.current_node = enumerated_list

    def _depart_ol(self):
        self.current_node = self.current_node.parent

    def _visit_li(self, attrs):
        list_item = nodes.list_item()
        self.current_node.append(list_item)
        self.current_node = list_item
        self._visit_p([])

    def _depart_li(self):
        self._depart_p()
        self.current_node = self.current_node.parent

    def _visit_table(self, attrs):
        table = nodes.table()
        self.current_node.append(table)
        self.current_node = table

    def _depart_table(self):
        self.current_node = self.current_node.parent

    def _visit_thead(self, attrs):
        thead = nodes.thead()
        self.current_node.append(thead)
        self.current_node = thead

    def _depart_thead(self):
        self.current_node = self.current_node.parent

    def _visit_tbody(self, attrs):
        tbody = nodes.tbody()
        self.current_node.append(tbody)
        self.current_node = tbody

    def _depart_tbody(self):
        self.current_node = self.current_node.parent

    def _visit_tr(self, attrs):
        row = nodes.row()
        self.current_node.append(row)
        self.current_node = row

    def _depart_tr(self):
        self.current_node = self.current_node.parent

    def _visit_th(self, attrs):
        entry = nodes.entry()
        self.current_node.append(entry)
        self.current_node = entry

    def _depart_th(self):
        self.current_node = self.current_node.parent

    def _visit_td(self, attrs):
        entry = nodes.entry()
        self.current_node.append(entry)
        self.current_node = entry

    def _depart_td(self):
        self.current_node = self.current_node.parent

    def _visit_div(self, attrs):
        pass

    def _depart_div(self):
        pass

    def _visit_pre(self, attrs):
        pass

    def _depart_pre(self):
        pass

    def _visit_span(self, attrs):
        pass

    def _depart_span(self):
        pass

    def _visit_blockquote(self, attrs):
        block_quote = nodes.block_quote()
        self.current_node.append(block_quote)
        self.current_node = block_quote

    def _depart_blockquote(self):
        self.current_node = self.current_node.parent

    def _visit_hr(self, attrs):
        transition = nodes.transition()
        self.current_node.append(transition)
        self.current_node = transition

    def _depart_hr(self):
        self.current_node = self.current_node.parent

    def _visit_br(self, attrs):
        text = nodes.Text('\n')
        self.current_node.append(text)
        self.current_node = text

    def _depart_br(self):
        self.current_node = self.current_node.parent


    # Node type enter/exit handlers
    def default_visit(self, mdnode):
        pass

    def default_depart(self, mdnode):
        """Default node depart handler

        If there is a matching ``visit_<type>`` method for a container node,
        then we should make sure to back up to it's parent element when the node
        is exited.
        """
        if mdnode.is_container():
            fn_name = 'visit_{0}'.format(mdnode.t)
            if not hasattr(self, fn_name):
                warn("Container node skipped: type={0}".format(mdnode.t))
            else:
                self.current_node = self.current_node.parent

    def visit_heading(self, mdnode):
        # Test if we're replacing a section level first
        if isinstance(self.current_node, nodes.section):
            if self.is_section_level(mdnode.level, self.current_node):
                self.current_node = self.current_node.parent

        title_node = nodes.title()
        title_node.line = mdnode.sourcepos[0][0]

        new_section = nodes.section()
        new_section.line = mdnode.sourcepos[0][0]
        new_section.append(title_node)

        self.add_section(new_section, mdnode.level)

        # Set the current node to the title node to accumulate text children/etc
        # for heading.
        self.current_node = title_node

    def depart_heading(self, _):
        """Finish establishing section

        Wrap up title node, but stick in the section node. Add the section names
        based on all the text nodes added to the title.
        """
        assert isinstance(self.current_node, nodes.title)
        # The title node has a tree of text nodes, use the whole thing to
        # determine the section id and names
        text = self.current_node.astext()
        if self.translate_section_name:
            text = self.translate_section_name(text)
        name = nodes.fully_normalize_name(text)
        section = self.current_node.parent
        section['names'].append(name)
        self.document.note_implicit_target(section, section)
        self.current_node = section

    def visit_text(self, mdnode):
        self.current_node.append(nodes.Text(mdnode.literal, mdnode.literal))

    def visit_softbreak(self, _):
        self.current_node.append(nodes.Text('\n'))

    def visit_paragraph(self, mdnode):
        p = nodes.paragraph(mdnode.literal)
        p.line = mdnode.sourcepos[0][0]
        self.current_node.append(p)
        self.current_node = p

    def visit_emph(self, _):
        n = nodes.emphasis()
        self.current_node.append(n)
        self.current_node = n

    def visit_strong(self, _):
        n = nodes.strong()
        self.current_node.append(n)
        self.current_node = n

    def visit_code(self, mdnode):
        n = nodes.literal(mdnode.literal, mdnode.literal)
        self.current_node.append(n)

    def visit_link(self, mdnode):
        ref_node = nodes.reference()
        # Check destination is supported for cross-linking and remove extension
        destination = mdnode.destination
        _, ext = splitext(destination)
        # TODO check for other supported extensions, such as those specified in
        # the Sphinx conf.py file but how to access this information?
        # TODO this should probably only remove the extension for local paths,
        # i.e. not uri's starting with http or other external prefix.
        if ext.replace('.', '') in self.supported:
            destination = destination.replace(ext, '')
        ref_node['refuri'] = destination
        # TODO okay, so this is acutally not always the right line number, but
        # these mdnodes won't have sourcepos on them for whatever reason. This
        # is better than 0 though.
        ref_node.line = self._get_line(mdnode)
        if mdnode.title:
            ref_node['title'] = mdnode.title
        next_node = ref_node

        url_check = urlparse(destination)
        if not url_check.scheme and not url_check.fragment:
            wrap_node = addnodes.pending_xref(
                reftarget=destination,
                reftype='any',
                refdomain=None,  # Added to enable cross-linking
                refexplicit=True,
                refwarn=True
            )
            # TODO also not correct sourcepos
            wrap_node.line = self._get_line(mdnode)
            if mdnode.title:
                wrap_node['title'] = mdnode.title
            wrap_node.append(ref_node)
            next_node = wrap_node

        self.current_node.append(next_node)
        self.current_node = ref_node

    def depart_link(self, mdnode):
        if isinstance(self.current_node.parent, addnodes.pending_xref):
            self.current_node = self.current_node.parent.parent
        else:
            self.current_node = self.current_node.parent

    def visit_image(self, mdnode):
        img_node = nodes.image()
        img_node['uri'] = mdnode.destination

        if mdnode.title:
            img_node['alt'] = mdnode.title

        self.current_node.append(img_node)
        self.current_node = img_node

    def visit_list(self, mdnode):
        list_node = None
        if (mdnode.list_data['type'] == "bullet"):
            list_node_cls = nodes.bullet_list
        else:
            list_node_cls = nodes.enumerated_list
        list_node = list_node_cls()
        list_node.line = mdnode.sourcepos[0][0]

        self.current_node.append(list_node)
        self.current_node = list_node

    def visit_item(self, mdnode):
        node = nodes.list_item()
        node.line = mdnode.sourcepos[0][0]
        self.current_node.append(node)
        self.current_node = node

    def visit_code_block(self, mdnode):
        kwargs = {}
        if mdnode.is_fenced and mdnode.info:
            kwargs['language'] = mdnode.info
        text = ''.join(mdnode.literal)
        if text.endswith('\n'):
            text = text[:-1]
        node = nodes.literal_block(text, text, **kwargs)
        self.current_node.append(node)

    def visit_block_quote(self, mdnode):
        q = nodes.block_quote()
        q.line = mdnode.sourcepos[0][0]
        self.current_node.append(q)
        self.current_node = q

    def visit_html(self, mdnode):
        raw_node = nodes.raw(mdnode.literal,
                             mdnode.literal, format='html')
        if mdnode.sourcepos is not None:
            raw_node.line = mdnode.sourcepos[0][0]
        self.current_node.append(raw_node)

    def visit_html_inline(self, mdnode):
        self.visit_html(mdnode)

    def visit_html_block(self, mdnode):
        self.visit_html(mdnode)

    def visit_thematic_break(self, _):
        self.current_node.append(nodes.transition())

    # Section handling
    def setup_sections(self):
        self._level_to_elem = {0: self.document}

    def add_section(self, section, level):
        parent_level = max(
            section_level for section_level in self._level_to_elem
            if level > section_level
        )
        parent = self._level_to_elem[parent_level]
        parent.append(section)
        self._level_to_elem[level] = section

        # Prune level to limit
        self._level_to_elem = dict(
            (section_level, section)
            for section_level, section in self._level_to_elem.items()
            if section_level <= level
        )

    def is_section_level(self, level, section):
        return self._level_to_elem.get(level, None) == section

    def _get_line(self, mdnode):
        while mdnode:
            if mdnode.sourcepos:
                return mdnode.sourcepos[0][0]
            mdnode = mdnode.parent
        return 0
