import unittest
from nose.tools import *
from ni.actions.base import Action, MoveCursorAction, EditAction
from ni.core.selection import Selection
from ni.core.document import Document
from ni.test.mocks import MockView


TEXT_DATA = u"""
old pond...
a frog leaps in
water's sound
""".strip()

#class MockMoveCursorAction(MoveCursorAction):
#    def move(self):
#        # Move one character to the right.
#        # Don't even bother checking if this is legal.
#        self.view.cursor_pos = (1, 0)
#
#class MockDelta(object):
#    def __init__(self, document):
#        self.document = document
#        self.line = self.document.get_line(0)
#
#    def do(self):
#        self.document.set_line(0, "hello")
#        self.document.invalidate(0)
#
#    def undo(self):
#        self.document.set_line(0, self.line)
#        self.document.invalidate(0)
#
#class MockEditAction(EditAction):
#    def do(self):
#        d = MockDelta(self.view.document)
#        d.do()
#        self.deltas.append(d)
#        self.view.cursor_pos = (5, 0)
#
#class TestBaseAction(unittest.TestCase):
#    def setUp(self):
#        self.editor = object()
#        self.document = Document(title='UNTITLED')
#        self.view = MockView(self.editor, self.document)
#
#    def test_new(self):
#        action = Action(self.view)
#        assert action.grouped == False
#        assert action.editor == self.editor
#        assert action.view == self.view
#
#    @raises(NotImplementedError)
#    def test_execute(self):
#        action = Action(self.view)
#        action.execute()
#
#class TestMoveCursorAction(unittest.TestCase):
#    def setUp(self):
#        self.editor = object()
#        self.document = Document(title='UNTITLED')
#        self.view = MockView(self.editor, self.document)
#
#    def test_new(self):
#        action = MoveCursorAction(self.view)
#        assert not action.is_select
#
#    def test_new_select(self):
#        action = MoveCursorAction(self.view, True)
#        assert action.is_select
#
#    @raises(NotImplementedError)
#    def test_execute(self):
#        action = MoveCursorAction(self.view)
#        action.execute()
#
#    def test_move(self):
#        action = MockMoveCursorAction(self.view)
#
#        # before we execute, the view hasn't been invalidated
#        assert self.view.is_valid
#
#        action.execute()
#
#        # after we execute, the view has been invalidated
#        assert not self.view.is_valid
#
#        # make sure we really didn't select anything
#        assert not self.view.selection
#
#    def test_select(self):
#        action = MockMoveCursorAction(self.view, True)
#        action.execute()
#
#        assert self.view.selection.start == (0, 0)
#        assert self.view.selection.end == (1, 0)
#
#class TestEditAction(unittest.TestCase):
#    def setUp(self):
#        self.editor = object()
#        self.document = Document(title='UNTITLED')
#        self.view = MockView(self.editor, self.document)
#
#        self.document.insert((0, 0), TEXT_DATA)
#
#    # base editaction
#
#    def test_new(self):
#        action = EditAction(self.view)
#        assert not action.is_executed
#
#    @raises(NotImplementedError)
#    def test_execute_unimplemented(self):
#        action = EditAction(self.view)
#        action.execute()
#
#    @raises(RuntimeError)
#    def test_undo_before_execute(self):
#        action = EditAction(self.view)
#        action.undo()
#        assert not self.view.is_valid
#
#    @raises(RuntimeError)
#    def test_redo_before_execute(self):
#        action = EditAction(self.view)
#        action.redo()
#        assert not self.view.is_valid
#
#    def test_delete_selection(self):
#        action = EditAction(self.view)
#        self.view.selection = Selection(self.document, (0, 0), (0, 1))
#        action.delete_selection()
#
#        assert self.document.get_line(0) == "a frog leaps in"
#        assert self.view.cursor_pos == (0, 0)
#
#    # real action
#
#    def test_execute(self):
#        action = MockEditAction(self.view)
#        action.execute()
#        assert self.document.get_line(0) == "hello"
#        assert self.view.cursor_pos == (5, 0)
#        assert not self.view.is_valid  # to see if execute invalidates the view
#
#    def test_undo(self):
#        action = MockEditAction(self.view)
#        action.execute()
#        self.view.is_valid = True # to see if undo invalidates the view
#        action.undo()
#        self.document.get_line(0) == "old pond..."
#        assert self.view.cursor_pos == (0, 0)
#        assert not self.view.is_valid
#
#    def test_redo(self):
#        action = MockEditAction(self.view)
#        action.execute()
#        action.undo()
#        self.view.is_valid = True # to see if redo invalidates the view
#        action.redo()
#        assert self.document.get_line(0) == "hello"
#        assert self.view.cursor_pos == (5, 0)
#        assert not self.view.is_valid

