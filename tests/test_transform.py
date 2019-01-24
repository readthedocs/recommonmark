from recommonmark.transform import AutoStructify, auto_code_block_eval_rst
from docutils.utils import new_document
import unittest


class DummyConfig(object):
    def __init__(self, config):
        if config is None:
            config = {}
        self.recommonmark_config = config


class DummyEnv(object):

    def __init__(self, config):
        self.config = config


class AutoStructifyTestCase(unittest.TestCase):

    def _make_one(self, recommonmark_config=None):
        document = new_document('test data')
        config = DummyConfig(recommonmark_config)
        document.settings.env = DummyEnv(config)
        transformer = AutoStructify(document)
        return transformer

    def test_init_uses_unmodified_default_config(self):
        transformer = self._make_one()
        assert transformer.config == transformer.default_config

    def test_init_overrides_default_config(self):
        transformer = self._make_one({'enable_auto_toc_tree': False})
        assert transformer.config != transformer.default_config
        assert transformer.config['enable_auto_toc_tree'] == False

    def test_init_extends_auto_code_block_transformers(self):
        transformers = {'plantuml': lambda x,y: x}
        transformer = self._make_one(
            {'auto_code_block_transformers': transformers})
        langs = list(
            transformer.config['auto_code_block_transformers'].keys())
        langs.sort()
        assert langs == ['eval_rst', 'math', 'plantuml']

    def test_init_overrides_default_auto_code_block_transformer(self):
        def dummy():
            pass
        transformer = self._make_one(
            {'auto_code_block_transformers': {'math': dummy}})

        should = {
            'math': dummy,
            'eval_rst': auto_code_block_eval_rst}

        assert transformer.config['auto_code_block_transformers'] == should

