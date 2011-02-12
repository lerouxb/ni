import os
import tempfile
import shutil
import unittest
from nose.tools import *
from ni.editors.base.settings import BaseSettings, load_settings_from_file


SETTINGS_TEXT = u"""
indent_width=4
tab_size=8
file_encoding=utf8
linesep=\\n
indent_spaces=True
most_recent_file=/home/leroux/projects/ni/test/mock.py
""".strip().encode('utf8')

EXPECTED_SETTINGS_PAIRS = [
    ('indent_width', 4),
    ('tab_size', 8),
    ('file_encoding', 'utf8'),
    ('linesep', '\n'),
    ('indent_spaces', True),
    ('most_recent_file', '/home/leroux/projects/ni/test/mock.py')
]

WORKSPACE_TEXT = u"""
name: ni
root-path: /home/leroux/projects/ni
exclude-globs:
    *.pyc
exclude-regulars:
filter-globs:
    Python: *.py
filter-regulars:
""".strip().encode('utf8')

class TestBaseSettings(unittest.TestCase):
    def setUp(self):
        self.settings_dir = tempfile.mkdtemp()
        handle, name = tempfile.mkstemp(dir=self.settings_dir, text=True)
        self.filename = name
        fle = open(name, 'w')
        try:
            fle.write(SETTINGS_TEXT)
            fle.close()

            self.settings = load_settings_from_file(self.filename, BaseSettings)

        finally:
            fle.close()

        workspaces_dir = self.settings.get_workspaces_dir()
        os.mkdir(workspaces_dir)
        workspace_filename = os.path.join(workspaces_dir, 'ni.workspace')
        fle = open(workspace_filename, 'w')
        fle.write(WORKSPACE_TEXT)
        fle.close()

    def tearDown(self):
        shutil.rmtree(self.settings_dir)

    ###

    def test_getattr(self):
        for k, v in EXPECTED_SETTINGS_PAIRS:
            assert getattr(self.settings, k) == v

    def test_getitem(self):
        for k, v in EXPECTED_SETTINGS_PAIRS:
            assert self.settings[k] == v

    @raises(KeyError)
    def test_getitem_fail(self):
        v = self.settings['xxx']

    def test_setitem(self):
        self.settings['indent_width'] = 2
        assert self.settings['indent_width'] == 2

    @raises(KeyError)
    def test_setitem_fail(self):
        self.settings['xxx'] = 'hello' # must raise KeyError

    def test_get_recent_files_path(self):
        expected_path = os.path.join(self.settings_dir, 'recent_files')
        assert self.settings.get_recent_files_path() == expected_path

    def test_get_workspaces_dir(self):
        expected_path = os.path.join(self.settings_dir, 'workspaces')
        assert self.settings.get_workspaces_dir() == expected_path

    def test_load_workspaces(self):
        workspaces = self.settings.load_workspaces()
        assert len(workspaces) == 1
        assert workspaces[0].name == 'ni'

    def test_validators(self):
        self.settings['linesep'] = r'\r\n'
        assert self.settings['linesep'] == '\r\n'

        self.settings['linesep'] = '\r\n'
        assert self.settings['linesep'] == '\r\n'

    #def test_formatters(self):
    #    pass

    def test_save(self):
        self.settings['indent_width'] = 2
        self.settings.save()

        new_settings = load_settings_from_file(self.filename, BaseSettings)
        assert new_settings['indent_width'] == 2

