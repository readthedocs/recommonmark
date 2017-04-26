"""Implement some common transforms on parsed AST."""
import os
import sys
import re
import sphinx
from .states import DummyStateMachine
from docutils import nodes, transforms
from docutils.statemachine import StringList
from docutils.parsers.rst import Parser
from docutils.utils import new_document


class AutoStructify(transforms.Transform):

    """Automatically try to transform blocks to sphinx directives.

    This class is designed to handle AST generated by CommonMarkParser.
    """
    # set to a high priority so it can be applied first for markdown docs
    default_priority = 1
    suffix_set = set(['md', 'rst'])

    default_config = {
        'enable_auto_doc_ref': True,
        'auto_toc_tree_section': None,
        'enable_auto_toc_tree': True,
        'enable_eval_rst': True,
        'enable_math': True,
        'enable_inline_math': True,
        'enable_table_extension': False,
        'commonmark_suffixes': ['.md'],
        'url_resolver': lambda x: x,
    }

    def parse_ref(self, ref):
        """Analyze the ref block, and return the information needed.

        Parameters
        ----------
        ref : nodes.reference

        Returns
        -------
        result : tuple of (str, str, str)
            The returned result is tuple of (title, uri, docpath).
            title is the display title of the ref.
            uri is the html uri of to the ref after resolve.
            docpath is the absolute document path to the document, if
            the target corresponds to an internal document, this can bex None
        """
        assert isinstance(ref, nodes.reference)
        title = None
        if len(ref.children) == 0:
            title = ref['name']
        elif isinstance(ref.children[0], nodes.Text):
            title = ref.children[0].astext()
        uri = ref['refuri']
        if uri.find('://') != -1:
            return (title, uri, None)
        anchor = None
        arr = uri.split('#')
        if len(arr) == 2:
            anchor = arr[1]
        if len(arr) > 2 or len(arr[0]) == 0:
            return (title, uri, None)
        uri = arr[0]

        abspath = os.path.abspath(os.path.join(self.file_dir, uri))
        relpath = os.path.relpath(abspath, self.root_dir)
        suffix = abspath.rsplit('.', 1)
        if len(suffix) == 2 and suffix[1] in AutoStructify.suffix_set and (
                os.path.exists(abspath) and abspath.startswith(self.root_dir)):
            # replace the path separator if running on non-UNIX environment
            if os.path.sep != '/':
                relpath = relpath.replace(os.path.sep, '/')
            docpath = '/' + relpath.rsplit('.', 1)[0]
            # rewrite suffix to html, this is suboptimal
            uri = docpath + '.html'
            if anchor is None:
                return (title, uri, docpath)
            else:
                return (title, uri + '#' + anchor, None)
        else:
            # use url resolver
            if self.url_resolver:
                uri = self.url_resolver(relpath)
            if anchor:
                uri += '#' + anchor
            return (title, uri, None)

    def auto_toc_tree(self, node):
        """Try to convert a list block to toctree in rst.

        This function detects if the matches the condition and return
        a converted toc tree node. The matching condition:
        The list only contains one level, and only contains references

        Parameters
        ----------
        node: nodes.Sequential
            A list node in the doctree

        Returns
        -------
        tocnode: docutils node
            The converted toc tree node, None if conversion is not possible.
        """
        if not self.config['enable_auto_toc_tree']:
            return None
        # when auto_toc_tree_section is set
        # only auto generate toctree under the specified section title
        sec = self.config['auto_toc_tree_section']
        if sec is not None:
            if node.parent is None:
                return None
            if not isinstance(node.parent, nodes.section):
                return None
            title = node.parent.children[0]
            if not isinstance(title, nodes.title):
                return None
            if title.astext().strip() != sec:
                return None

        numbered = None
        if isinstance(node, nodes.bullet_list):
            numbered = 0
        elif isinstance(node, nodes.enumerated_list):
            numbered = 1

        if numbered is None:
            return None
        refs = []
        for nd in node.children[:]:
            assert isinstance(nd, nodes.list_item)
            if len(nd.children) != 1:
                return None
            par = nd.children[0]
            if not isinstance(par, nodes.paragraph):
                return None
            if len(par.children) != 1:
                return None
            ref = par.children[0]
            if not isinstance(ref, nodes.reference):
                return None
            title, uri, docpath = self.parse_ref(ref)
            if title is None or uri.startswith('#'):
                return None
            if docpath:
                refs.append((title, docpath))
            else:
                refs.append((title, uri))
        self.state_machine.reset(self.document,
                                 node.parent,
                                 self.current_level)
        return self.state_machine.run_directive(
            'toctree',
            options={'maxdepth': 1, 'numbered': numbered},
            content=['%s <%s>' % (k, v) for k, v in refs])

    def auto_doc_ref(self, node):
        """Try to convert a reference to docref in rst.

        Parameters
        ----------
        node : nodes.reference
           A reference node in doctree.

        Returns
        -------
        tocnode: docutils node
            The converted toc tree node, None if conversion is not possible.
        """
        if not self.config['enable_auto_doc_ref']:
            return None
        assert isinstance(node, nodes.reference)
        title, uri, docpath = self.parse_ref(node)
        if title is None:
            return None
        if docpath:
            content = u'%s <%s>' % (title, docpath)
            self.state_machine.reset(self.document,
                                     node.parent,
                                     self.current_level)
            return self.state_machine.run_role('doc', content=content)
        else:
            # inplace modify uri
            node['refuri'] = uri
            return None

    def auto_inline_code(self, node):
        """Try to automatically generate nodes for inline literals.

        Parameters
        ----------
        node : nodes.literal
            Original codeblock node
        Returns
        -------
        tocnode: docutils node
            The converted toc tree node, None if conversion is not possible.
        """
        assert isinstance(node, nodes.literal)
        if len(node.children) != 1:
            return None
        content = node.children[0]
        if not isinstance(content, nodes.Text):
            return None
        content = content.astext().strip()
        if content.startswith('$') and content.endswith('$'):
            if not self.config['enable_inline_math']:
                return None
            content = content[1:-1]
            self.state_machine.reset(self.document,
                                     node.parent,
                                     self.current_level)
            return self.state_machine.run_role('math', content=content)
        else:
            return None

    def auto_code_block(self, node):
        """Try to automatically generate nodes for codeblock syntax.

        Parameters
        ----------
        node : nodes.literal_block
            Original codeblock node
        Returns
        -------
        tocnode: docutils node
            The converted toc tree node, None if conversion is not possible.
        """
        assert isinstance(node, nodes.literal_block)
        original_node = node
        if 'language' not in node:
            return None
        self.state_machine.reset(self.document,
                                 node.parent,
                                 self.current_level)
        content = node.rawsource.split('\n')
        language = node['language']
        if language == 'math':
            if self.config['enable_math']:
                return self.state_machine.run_directive(
                    'math', content=content)
        elif language == 'eval_rst':
            if self.config['enable_eval_rst']:
                # allow embed non section level rst
                node = nodes.section()
                self.state_machine.state.nested_parse(
                    StringList(content, source=original_node.source),
                    0, node=node, match_titles=False)
                return node.children[:]
        else:
            match = re.search('[ ]?[\w_-]+::.*', language)
            if match:
                parser = Parser()
                new_doc = new_document(None, self.document.settings)
                newsource = u'.. ' + match.group(0) + '\n' + node.rawsource
                parser.parse(newsource, new_doc)
                return new_doc.children[:]
            else:
                return self.state_machine.run_directive(
                    'code-block', arguments=[language],
                    content=content)
        return None

    def table_extension(self, node):
        """Convert markdown table to reStructuredText on the fly and create a docnode containing this table

        Parameters
        ----------
        node : nodes.paragraph
            A paragraph containing a Markdown table (begins and ends with |)
        Returns
        -------
        tocnode: docutils node
            The converted toc tree node, None if conversion is not possible.
        """
        if not self.config['enable_table_extension']:
            return None

        # Python 2&3 compatibility
        if sys.version_info[0] == 3:
            string_type = str
        else:
            string_type = basestring

        original_node = node

        rows = []
        max_width = 0
        max_cells = 0

        current_row = []
        current_cell = ''
        for child in node.children:
            if child == '\n':
                # determine number of cells
                if len(current_row) > max_cells:
                    max_cells = len(current_row)
                # update max_width
                for cell in current_row:
                    if len(cell) > max_width:
                        max_width = len(cell)
                # Finally append line and reset it
                rows.append(current_row)
                current_row = []

            elif isinstance(child, string_type):
                stripped_child = child.strip()
                if stripped_child.startswith('|') and current_cell:
                    # If the line starts with | it means the previous cell is finished -> Append it to current row
                    current_row.append(current_cell)
                    current_cell = ''

                elements = stripped_child.split('|')
                if len(elements) > 1:
                    for i in range(len(elements)):
                        e = elements[i]
                        if e:
                            if 0 < i < (len(elements) - 1):
                                # If text is between two | add it as complete text
                                current_row.append(e)
                            else:
                                # Otherwise, append text to current_cell
                                current_cell += e
                elif len(elements) == 1:
                    current_cell += elements[0]

                if stripped_child.endswith('|') and not stripped_child.startswith('|') and current_cell:
                    # If the line ends with | it means the previous cell is finished -> Append it to current row
                    current_row.append(current_cell)
                    current_cell = ''

            elif isinstance(child, nodes.reference):
                # Convert reference to rst reference
                current_cell += ' `' + child.attributes['name'] + ' <' + child.attributes['refuri'] + '>`_ '
            elif isinstance(child, sphinx.addnodes.pending_xref):
                current_cell += ' `' + child.children[0] + ' <' + child.attributes['reftarget'] + '>`_ '
            else:
                # Invalid child within table -> Abort
                return None

        # Finish last row
        # determine number of cells
        if len(current_row) > max_cells:
            max_cells = len(current_row)
        # update max_width
        for cell in current_row:
            if len(cell) > max_width:
                max_width = len(cell)
        # Finally append line
        rows.append(current_row)

        # Convert to rst
        max_width += 2  # Because a space will be added on both sides of the cell
        rst_lines = []
        no_border = False
        heading_pattern = re.compile('^[- ]+$', re.MULTILINE)
        for line in rows:
            if heading_pattern.search(''.join(line)):
                rst_lines.append(('+' + ('=' * max_width)) * max_cells + '+')
                no_border = True
            else:
                if not no_border:
                    rst_lines.append(('+' + ('-' * max_width)) * max_cells + '+')
                line_str = '|'
                for cell in line:
                    line_str += ' ' + cell + (' ' * (max_width - len(cell) - 2)) + ' |'
                rst_lines.append(line_str)
                no_border = False
        rst_lines.append(('+' + ('-' * max_width)) * max_cells + '+')
        rst_lines.append('')

        # Create new node
        self.state_machine.reset(self.document,
                                 node.parent,
                                 self.current_level)

        node = nodes.section()
        self.state_machine.state.nested_parse(
            StringList(rst_lines, source=original_node.source),
            0, node=node, match_titles=False)

        return node.children[:]

    def find_replace(self, node):
        """Try to find replace node for current node.

        Parameters
        ----------
        node : docutil node
            Node to find replacement for.

        Returns
        -------
        nodes : node or list of node
            The replacement nodes of current node.
            Returns None if no replacement can be found.
        """
        newnode = None
        if isinstance(node, nodes.Sequential):
            newnode = self.auto_toc_tree(node)
        elif isinstance(node, nodes.reference):
            newnode = self.auto_doc_ref(node)
        elif isinstance(node, nodes.literal_block):
            newnode = self.auto_code_block(node)
        elif isinstance(node, nodes.literal):
            newnode = self.auto_inline_code(node)
        elif isinstance(node, nodes.paragraph) and node.rawsource.startswith('|') and node.rawsource.endswith('|'):
            newnode = self.table_extension(node)
        return newnode

    def traverse(self, node):
        """Traverse the document tree rooted at node.

        node : docutil node
            current root node to traverse
        """
        old_level = self.current_level
        if isinstance(node, nodes.section):
            if 'level' in node:
                self.current_level = node['level']
        to_visit = []
        to_replace = []
        for c in node.children[:]:
            newnode = self.find_replace(c)
            if newnode is not None:
                to_replace.append((c, newnode))
            else:
                to_visit.append(c)

        for oldnode, newnodes in to_replace:
            node.replace(oldnode, newnodes)

        for child in to_visit:
            self.traverse(child)
        self.current_level = old_level

    def apply(self):
        """Apply the transformation by configuration."""
        source = self.document['source']

        self.reporter = self.document.reporter
        self.reporter.info('AutoStructify: %s' % source)

        config = self.default_config.copy()
        try:
            new_cfg = self.document.settings.env.config.recommonmark_config
            config.update(new_cfg)
        except:
            self.reporter.warning('recommonmark_config not setted,'
                                  ' proceed default setting')

        # only transform markdowns
        if not source.endswith(tuple(config['commonmark_suffixes'])):
            return

        self.url_resolver = config['url_resolver']
        assert callable(self.url_resolver)

        self.config = config
        self.state_machine = DummyStateMachine()
        self.current_level = 0
        self.file_dir = os.path.abspath(os.path.dirname(self.document['source']))
        self.root_dir = os.path.abspath(self.document.settings.env.srcdir)
        self.traverse(self.document)
