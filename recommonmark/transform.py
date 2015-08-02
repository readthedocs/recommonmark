"""Implement some common transforms on parsed AST."""
import os
import sys
from states import DummyStateMachine
from docutils import nodes, transforms

class AutoStructify(transforms.Transform):
    """Automatically try to transform blocks to sphinx directives.

    This class is designed to handle AST generated by CommonMarkParser.
    """
    default_priority = 860
    url_resolver = None
    suffix_set = set(['md', 'rst'])

    @staticmethod
    def setup_url_resolver(fn):
        """Setup url resolver for AutoStructify.

        url_resolver function takes a url and returns a resolved url.
        This can be used to map link to code to internet pages such as github.

        Parameters
        ----------
        fn : callable
            Url resolver function.
        """
        assert callable(fn)
        AutoStructify.url_resolver = [fn]

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
        uri = arr[0]
        if len(arr) > 2 or len(uri) == 0:
            return (title, uri, None)

        abspath = os.path.abspath(os.path.join(self.file_dir, uri))
        relpath = os.path.relpath(abspath, self.root_dir)
        suffix = abspath.rsplit('.', 1)
        if len(suffix) == 2 and suffix[1] in AutoStructify.suffix_set and (
            os.path.exists(abspath) and abspath.startswith(self.root_dir)):
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
                uri = self.url_resolver[0](relpath)
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

    def traverse(self, node):
        """Traverse the document tree rooted at node.

        node : docutil node
            current root node to traverse
        """
        newnode = None
        old_level = self.current_level
        if isinstance(node, nodes.section):
            if 'level' in node:
                self.current_level = node['level']
        elif isinstance(node, nodes.Sequential):
            newnode = self.auto_toc_tree(node)
        elif isinstance(node, nodes.reference):
            newnode = self.auto_doc_ref(node)

        if newnode:
            node.replace_self(newnode)
        else:
            for c in node.children[:]:
                self.traverse(c)
        self.current_level = old_level

    def apply(self):
        self.state_machine = DummyStateMachine()
        self.current_level = 0
        self.file_dir = os.path.abspath(os.path.dirname(self.document['source']))
        self.root_dir = os.path.abspath(self.document.settings.env.srcdir)
        self.traverse(self.document)
        print self.document.pformat()
