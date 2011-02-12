import unittest
from nose.tools import *
from ni.actions.base import EditAction
from ni.editors.base.editor import Editor, actions_are_grouped
from ni.test.mocks import MockView


class MockEditAction(EditAction):
    def execute(self):
        pass

def test_actions_are_grouped_yes():
    editor = object()
    document = object()
    view = MockView(editor, document)

    action1 = MockEditAction(view)
    action1.grouped = hash(action1)
    action2 = MockEditAction(view)
    action2.grouped = hash(action1)

    assert actions_are_grouped(action1, action2)

def test_actions_are_grouped_no():
    editor = object()
    document = object()
    view = MockView(editor, document)

    action1 = MockEditAction(view)
    action2 = MockEditAction(view)

    assert not actions_are_grouped(action1, action2)

class TestEditor(unittest.TestCase):
    def setUp(self):
        self.editor = Editor()

    #def test_switch_to_previous_view(self):
    #    pass

    #def test_switch_to_next_view(self):
    #    pass

    #def test_cancel_search(self):
    #    pass

    def test_undo(self):
        pass

    def test_redo(self):
        pass

    def test_get_next_title(self):
        assert self.editor.get_next_title() == 'UNTITLED 1'
        assert self.editor.get_next_title() == 'UNTITLED 2'
        assert self.editor.get_next_title() == 'UNTITLED 3'

