import os
import unittest
from nose.tools import *
from ni.test.mocks import MockView, InterfaceLoggingMock
from ni.actions.defaultactions import *
from ni.core.document import Document
from ni.core.selection import Selection


TEXT_DATA = u"""
old pond...
a frog leaps in
water's sound
""".strip()

LAST_DOC_POS = (13, 2)

FIRST_LINE_END = (11, 0)
SECOND_LINE_END = (15, 1)

EXTRA_LINE = u"    this has spaces before and after    "
EXTRA_LINE_START = (0, 3)
EXTRA_LINE_FIRST_CHAR = (4, 3)

EXTRA_LINE_END = (40, 3)
EXTRA_LINE_LAST_CHAR = (36, 3)


class MockDialog(object):
    def __init__(self):
        self.show_called = False

    def show(self):
        self.show_called = True

class MockSettings(object):
    def __init__(self):
        self.indent_width = 4
        self.tab_size = 8

class MockEditor(InterfaceLoggingMock):
    def __init__(self):
        super(MockEditor, self).__init__()

        self.settings = MockSettings()

        self.open_dialog = MockDialog()
        self.switch_dialog = MockDialog()
        self.save_dialog = MockDialog()
        self.documents_dialog = MockDialog()
        self.goto_dialog = MockDialog()
        self.add_workspace_dialog = MockDialog()
        self.edit_workspace_dialog = MockDialog()
        self.preferences_dialog = MockDialog()
        self.find_dialog = MockDialog()

        self.previous_view = None

        self.views = []


class TestDefaultActions(unittest.TestCase):
    def setUp(self):
        self.editor = MockEditor()
        self.document = Document(title='UNTITLED')
        self.view = MockView(self.editor, self.document)
        self.editor.views.append(self.view)

        self.document.insert(0, TEXT_DATA)

    ###

    def test_Undo(self):
        action = Undo(self.view)
        action.execute()
        args, kwargs = self.editor.methods['undo']
        assert len(args) == 1 and not kwargs.keys()
        assert isinstance(args[0], MockView)

    def test_Redo(self):
        action = Redo(self.view)
        action.execute()
        args, kwargs = self.editor.methods['redo']
        assert len(args) == 1 and not kwargs.keys()
        assert isinstance(args[0], MockView)

    def test_SwitchToRecentDocument_None(self):
        action = SwitchToRecentDocument(self.view)
        action.execute()
        # by default there is no previous view, so we shouldn't have switched
        assert not self.editor.methods.has_key('switch_current_view')

    def test_SwitchToRecentDocument(self):
        self.editor.previous_view = self.view
        action = SwitchToRecentDocument(self.view)
        action.execute()
        args, kwargs = self.editor.methods['switch_current_view']
        assert len(args) == 1 and not kwargs.keys()
        assert args[0] == self.view

    def test_SwitchToPreviousDocument(self):
        action = SwitchToPreviousDocument(self.view)
        action.execute()
        args, kwargs = self.editor.methods['switch_to_previous_view']
        assert not args and not kwargs.keys()

    def test_SwitchToPreviousDocument_no_views(self):
        self.editor.views = []
        action = SwitchToPreviousDocument(self.view)
        action.execute()
        # the editor has no views, so we couldn't have switched
        assert not self.editor.methods.has_key('switch_to_previous_view')

    def test_SwitchToNextDocument(self):
        action = SwitchToNextDocument(self.view)
        action.execute()
        args, kwargs = self.editor.methods['switch_to_next_view']
        assert not args and not kwargs.keys()

    def test_SwitchToNextDocument_no_views(self):
        self.editor.views = []
        action = SwitchToNextDocument(self.view)
        action.execute()
        # the editor has no views, so we couldn't have switched
        assert not self.editor.methods.has_key('switch_to_next_view')

    def test_CreateNewDocument(self):
        action = CreateNewDocument(self.view)
        action.execute()
        args, kwargs = self.editor.methods['new_view']
        assert not args and not kwargs.keys()

    def test_CloseDocument(self):
        action = CloseDocument(self.view)
        action.execute()
        args, kwargs = self.editor.methods['close_view']
        assert not args and not kwargs.keys()

    def test_OpenDocument(self):
        action = OpenDocument(self.view)
        action.execute()
        assert self.editor.open_dialog.show_called

    def test_SwitchDocument(self):
        action = SwitchDocument(self.view)
        action.execute()
        assert self.editor.switch_dialog.show_called

    def test_SaveDocument_unsaved(self):
        action = SaveDocument(self.view)
        action.execute()
        assert self.editor.save_dialog.show_called

    def test_SaveDocument_saved(self):
        location = '/tmp/haiku.txt'
        self.document.location = location
        try:
            action = SaveDocument(self.view)
            action.execute()
            assert not self.view.is_valid   # must trigger a redraw
            assert os.path.exists(location) # must have saved
        finally:
            os.unlink(location)

    def test_SaveDocumentAs(self):
        action = SaveDocumentAs(self.view)
        action.execute()

        # when saving a document as something else, we're making a copy of the
        # current view...
        args, kwargs = self.editor.methods['copy_view']
        assert not args and not kwargs.keys()

        # ...and we're choosing where to save it
        assert self.editor.save_dialog.show_called

    def test_ListDocuments(self):
        action = ListDocuments(self.view)
        action.execute()

        assert self.editor.documents_dialog.show_called

    def test_GoToLine(self):
        action = GoToLine(self.view)
        action.execute()

        assert self.editor.goto_dialog.show_called

    def test_AddWorkspace(self):
        action = AddWorkspace(self.view)
        action.execute()

        assert self.editor.add_workspace_dialog.show_called

    def test_EditWorkspace(self):
        action = EditWorkspace(self.view)
        action.execute()

        assert self.editor.edit_workspace_dialog.show_called

    def test_Preferences(self):
        action = Preferences(self.view)
        action.execute()

        assert self.editor.preferences_dialog.show_called

    def test_FindorReplace(self):
        action = FindorReplace(self.view)
        action.execute()

        assert self.editor.find_dialog.show_called

    def test_ExitEditor(self):
        action = ExitEditor(self.view)
        action.execute()

        args, kwargs = self.editor.methods['exit']
        assert not args and not kwargs.keys()

    def test_ToggleSidebar(self):
        action = ToggleSidebar(self.view)
        action.execute()

        args, kwargs = self.editor.methods['toggle_sidebar']
        assert not args and not kwargs

    def test_ToggleLineNumbers(self):
        action = ToggleLineNumbers(self.view)
        action.execute()

        args, kwargs = self.editor.methods['toggle_gutter']
        assert not args and not kwargs

    def test_ToggleStatusbar(self):
        action = ToggleStatusbar(self.view)
        action.execute()

        args, kwargs = self.editor.methods['toggle_statusbar']
        assert not args and not kwargs

    def test_ToggleRightMargin(self):
        action = ToggleRightMargin(self.view)
        action.execute()

        args, kwargs = self.editor.methods['toggle_margin']
        assert not args and not kwargs

#    def test_SelectWord(self):
#        # we just test that it comes up with a selection, invalidates the view
#        # and sets cursor_pos and last_x_pos.
#        # This isn't the place to stress-test get_word_range and
#        # char_pos_to_tab_pos
#
#        before_cursor_pos = self.view.cursor_pos
#        before_last_x_pos = self.view.last_x_pos
#
#        action = SelectWord(self.view)
#        action.execute()
#
#        assert self.view.selection
#        assert not self.view.is_valid
#        assert before_cursor_pos != self.view.cursor_pos
#        assert before_last_x_pos != self.view.last_x_pos
#
#    def test_SelectAll(self):
#        action = SelectAll(self.view)
#        action.execute()
#
#        assert self.view.selection.get_content() == TEXT_DATA
#
#    def test_CancelSelection(self):
#        # Is this good practice? Should I use a mock or something? Perhaps
#        # just throw in any object and just make sure it gets cleared?
#        start = (0, 0)
#        end = (9, 0)
#        self.view.selection = Selection(self.document, start, end)
#
#        action = CancelSelection(self.view)
#        action.execute()
#
#        assert not self.view.selection
#
#    def test_MoveCursor(self):
#        # should I test with select=True?
#        # that gets handled in the base action...
#
#        pos = LAST_DOC_POS
#        action = MoveCursor(self.view, pos)
#        action.execute()
#
#        assert self.view.cursor_pos == pos
#
#    def test_MoveCursorUp(self):
#        self.view.cursor_pos = (1, 2)
#        self.view.last_x_pos = 1
#
#        action = MoveCursorUp(self.view)
#        action.execute()
#
#        # the preferred x pos is on the line, so we can set it
#        self.view.cursor_pos = (1, 1)
#
#    def test_MoveCursorUp_top(self):
#        self.view.cursor_pos = (0, 0)
#
#        action = MoveCursorUp(self.view)
#        action.execute()
#
#        # we started at the top and we should still be at the top
#        assert self.view.cursor_pos == (0, 0)
#
#    def test_MoveCursorUp_last_x_pos(self):
#        self.view.cursor_pos = (15, 1)
#        self.view.last_x_pos = 15
#
#        action = MoveCursorUp(self.view)
#        action.execute()
#
#        # the preferred x pos is not on the line,
#        # so we move to the end of theline
#        self.view.cursor_pos = FIRST_LINE_END
#
#    def test_MoveCursorDown(self):
#        self.view.cursor_pos = (1, 1)
#        self.view.last_x_pos = 1
#
#        action = MoveCursorDown(self.view)
#        action.execute()
#
#        # the preferred x pos is on the line, so we can set it
#        self.view.cursor_pos = (1, 2)
#
#    def test_MoveCursorDown_bottom(self):
#        self.view.cursor_pos = (0, 2)
#
#        action = MoveCursorDown(self.view)
#        action.execute()
#
#        # we started at the bottom and we should still be at the bottom
#        assert self.view.cursor_pos == (0, 2)
#
#    def test_MoveCursorDown_last_x_pos(self):
#        self.view.cursor_pos = (15, 1)
#        self.view.last_x_pos = 15
#
#        action = MoveCursorDown(self.view)
#        action.execute()
#
#        # the preferred x pos is not on the line,
#        # so we move to the end of theline
#        self.view.cursor_pos = LAST_DOC_POS
#
#    def test_MoveCursorLeft(self):
#        # not going to test all the edge cases, because that happens in
#        # prev_pos which is tested elsewhere
#
#        self.view.cursor_pos = LAST_DOC_POS
#
#        action = MoveCursorLeft(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == (LAST_DOC_POS[0]-1, LAST_DOC_POS[1])
#
#    def test_MoveCursorRight(self):
#        # not going to test all the edge cases, because that happens in
#        # next_pos which is tested elsewhere
#
#        self.view.cursor_pos = (0, 0)
#
#        action = MoveCursorRight(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == (1, 0)
#
#    def test_MoveCursorWordLeft_start_doc(self):
#        self.view.cursor_pos = (0, 0)
#
#        action = MoveCursorWordLeft(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == (0, 0) # can't move left
#
#    def test_MoveCursorWordLeft_start_line(self):
#        self.view.cursor_pos = (0, 1) # start of second line
#
#        action = MoveCursorWordLeft(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == FIRST_LINE_END # end of first line
#
#    def test_MoveCursorWordLeft_middle(self):
#        # this uses get_word_range and it is up to those tests to make sure
#        # that works with all the corner cases. I think.
#
#        self.view.cursor_pos = (6, 0) # po|nd
#
#        action = MoveCursorWordLeft(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == (4, 0) # |pond
#
#    def test_MoveCursorWordRight_end_doc(self):
#        self.view.cursor_pos = LAST_DOC_POS
#
#        action = MoveCursorWordRight(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == LAST_DOC_POS # can't move right
#
#    def test_MoveCursorWordRight_end_line(self):
#        self.view.cursor_pos = FIRST_LINE_END # end of first line
#
#        action = MoveCursorWordRight(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == (0, 1) # start of second line
#
#    def test_MoveCursorWordRight_middle(self):
#        # this uses get_word_range and it is up to those tests to make sure
#        # that works with all the corner cases. I think.
#
#        self.view.cursor_pos = (6, 0) # po|nd
#
#        action = MoveCursorWordRight(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == (8, 0) # pond|
#
#    def test_MoveCursorLineStart_first_char_from_middle(self):
#        # we're somewhere in the middle of a line and it should go to the first
#        # non-space character
#
#        self.document.insert(EXTRA_LINE_START, EXTRA_LINE)
#
#        self.view.cursor_pos = (10, 3) # just somewhere inside the last line
#        action = MoveCursorLineStart(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == EXTRA_LINE_FIRST_CHAR
#
#    def test_MoveCursorLineStart_real_start_from_first_char(self):
#        # we're on the first non-space character, so we should be moved to the
#        # actual start of the line (x position 0)
#
#        self.document.insert(EXTRA_LINE_START, EXTRA_LINE)
#
#        self.view.cursor_pos = EXTRA_LINE_FIRST_CHAR
#        action = MoveCursorLineStart(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == EXTRA_LINE_START
#
#    def test_MoveCursorLineStart_first_char_from_real_start(self):
#        # we're at x position 0, so we should be moved to the first non-space
#        # character
#
#        self.document.insert(EXTRA_LINE_START, EXTRA_LINE)
#
#        self.view.cursor_pos = EXTRA_LINE_START
#        action = MoveCursorLineStart(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == EXTRA_LINE_FIRST_CHAR
#
#    def test_MoveCursorLineEnd_first_char_from_middle(self):
#        # we're somewhere in the middle of a line and it should go to after
#        # the last non-space character
#
#        self.document.insert(EXTRA_LINE_START, EXTRA_LINE)
#
#        self.view.cursor_pos = (10, 3) # just somewhere inside the last line
#        action = MoveCursorLineEnd(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == EXTRA_LINE_LAST_CHAR
#
#    def test_MoveCursorLineEnd_real_start_from_last_char(self):
#        # we're after the last non-space character, so we should be moved to
#        # after the last character (whitespace included)
#
#        self.document.insert(EXTRA_LINE_START, EXTRA_LINE)
#
#        self.view.cursor_pos = EXTRA_LINE_LAST_CHAR
#        action = MoveCursorLineEnd(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == EXTRA_LINE_END
#
#    def test_MoveCursorLineEnd_first_char_from_real_end(self):
#        # we're at after the last character (spaces included) of the last line
#        # and we should be moved to after the last non-space char
#
#        self.document.insert(EXTRA_LINE_START, EXTRA_LINE)
#
#        self.view.cursor_pos = EXTRA_LINE_END
#        action = MoveCursorLineEnd(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == EXTRA_LINE_LAST_CHAR
#
#    def test_MoveCursorStart(self):
#        self.view.cursor_pos = (5, 2) # somewhere random
#        action = MoveCursorStart(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == (0, 0)
#
#    def test_MoveCursorEnd(self):
#        self.view.cursor_pos = (5, 2) # somewhere random
#        action = MoveCursorEnd(self.view)
#        action.execute()
#
#        assert self.view.cursor_pos == LAST_DOC_POS
#
#    def test_MoveCursorPageUp(self):
#        # TODO
#        pass
#
#    def test_MoveCursorPageDown(self):
#        # TODO
#        pass
#
#    def test_InsertText(self):
#        text = "hello"
#        self.view.cursor_pos = (0, 0)
#        action = InsertText(self.view, text)
#
#        action.execute()
#        assert self.document.get_content() == text + TEXT_DATA
#        assert self.view.cursor_pos == (5, 0)
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == (0, 0)
#
#    def test_InsertText_override_selection(self):
#        # select the second line
#        self.view.selection = Selection(self.document, (0, 1), SECOND_LINE_END)
#        self.cursor_pos = SECOND_LINE_END # as if we just selected the line
#
#        text = "hello"
#        action = InsertText(self.view, text)
#
#        action.execute()
#        assert self.document.get_line(1) == 'hello'
#        assert not self.view.selection
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.cursor_pos == SECOND_LINE_END

    def test_CopyToClipboard(self):
        action = CopyToClipboard(self.view)
        action.execute()

        args, kwargs = self.editor.methods['copy_to_clipboard']
        assert len(args) == 1 and isinstance(args[0], MockView) and not kwargs

    def test_PasteFromClipboard(self):
        action = PasteFromClipboard(self.view)
        action.execute()

        args, kwargs = self.editor.methods['paste_from_clipboard']
        assert len(args) == 1 and isinstance(args[0], MockView) and not kwargs

    def test_CutToClipboard(self):
        # select the second line
        self.view.selection = Selection(self.document, (0, 1), SECOND_LINE_END)
        self.cursor_pos = SECOND_LINE_END # as if we just selected the line

        action = CutToClipboard(self.view)

        action.execute()
        assert self.document.get_line(1) == ''

        action.undo()
        assert self.document.content == TEXT_DATA

        args, kwargs = self.editor.methods['copy_to_clipboard']
        assert len(args) == 1 and isinstance(args[0], MockView) and not kwargs

    def test_DeleteSelection(self):
        # select everything
        self.view.selection = Selection(self.document, (0, 0), LAST_DOC_POS)
        self.view.cursor_pos = LAST_DOC_POS

        action = DeleteSelection(self.view)
        action.execute()
        assert not self.document.content

        action.undo()
        assert self.document.content == TEXT_DATA

#    def test_DeleteTextForward_middle(self):
#        expected_line = 'old pond..' # deleted a '.'
#        self.view.cursor_pos = (8, 0)
#
#        action = DeleteTextForward(self.view)
#        action.execute()
#
#        assert self.document.get_line(0) == expected_line
#        assert self.view.cursor_pos == (8, 0)
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == (8, 0)
#
#    def test_DeleteTextForward_end_of_line(self):
#        expected_line = self.document.get_line(0) + self.document.get_line(1)
#        self.view.cursor_pos = FIRST_LINE_END
#
#        action = DeleteTextForward(self.view)
#        action.execute()
#
#        assert self.document.get_line(0) == expected_line
#        assert len(self.document.lines) == 2
#        assert self.view.cursor_pos == FIRST_LINE_END
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == FIRST_LINE_END
#
#
#    def test_DeleteTextForward_end_of_doc(self):
#        self.view.cursor_pos = LAST_DOC_POS
#
#        action = DeleteTextForward(self.view)
#        action.execute()
#
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == LAST_DOC_POS
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == LAST_DOC_POS
#
#    def test_DeleteTextForward_selection(self):
#         # select everything
#        self.view.selection = Selection(self.document, (0, 0), LAST_DOC_POS)
#        self.view.cursor_pos = LAST_DOC_POS
#
#        action = DeleteTextForward(self.view)
#        action.execute()
#        assert not self.document.get_content()
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#
#    def test_DeleteTextBackward_middle(self):
#        expected_line = 'old pon...' # deleted a '.'
#        self.view.cursor_pos = (8, 0)
#
#        action = DeleteTextBackward(self.view)
#        action.execute()
#
#        assert self.document.get_line(0) == expected_line
#        assert self.view.cursor_pos == (7, 0)
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == (8, 0)
#
#    def test_DeleteTextBackward_start_of_line(self):
#        expected_line = self.document.get_line(0) + self.document.get_line(1)
#        self.view.cursor_pos = (0, 1) # start of second line
#
#        action = DeleteTextBackward(self.view)
#        action.execute()
#
#        assert self.document.get_line(0) == expected_line
#        assert len(self.document.lines) == 2
#        assert self.view.cursor_pos == FIRST_LINE_END
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == (0, 1)
#
#    def test_DeleteTextBackward_start_of_doc(self):
#        self.view.cursor_pos = (0, 0)
#
#        action = DeleteTextBackward(self.view)
#        action.execute()
#
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == (0, 0)
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == (0, 0)
#
#    def test_DeleteTextBackward_selection(self):
#         # select everything
#        self.view.selection = Selection(self.document, (0, 0), LAST_DOC_POS)
#        self.view.cursor_pos = LAST_DOC_POS
#
#        action = DeleteTextBackward(self.view)
#        action.execute()
#        assert not self.document.get_content()
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#
#    def test_Indent(self):
#        self.view.cursor_pos = (0, 0)
#        action = Indent(self.view)
#
#        action.execute()
#        assert self.view.cursor_pos == (4, 0)
#        assert self.document.get_content() == '    '+TEXT_DATA
#
#        action.undo()
#        assert self.view.cursor_pos == (0, 0)
#        assert self.document.get_content() == TEXT_DATA
#
#
#    def test_Indent_selection(self):
#        # select everything
#        self.view.selection = Selection(self.document, (0, 0), LAST_DOC_POS)
#        self.view.cursor_pos = LAST_DOC_POS
#
#        lines = []
#        for line in self.document.get_content().split('\n'):
#            lines.append(line)
#
#        action = Indent(self.view)
#
#        action.execute()
#        for y, line in enumerate(lines):
#            assert self.document.get_line(y) == '    '+line
#        assert self.view.cursor_pos == (LAST_DOC_POS[0]+4, LAST_DOC_POS[1])
#
#        action.undo()
#        assert self.document.get_content() == TEXT_DATA
#        assert self.view.cursor_pos == LAST_DOC_POS
#
#    def test_Unindent(self):
#        self.document.set_line(0, '    '+self.document.get_line(0))
#        self.view.cursor_pos = (4, 0)
#        action = Unindent(self.view)
#
#        action.execute()
#        assert self.view.cursor_pos == (0, 0)
#        assert self.document.get_content() == TEXT_DATA
#
#        action.undo()
#        assert self.view.cursor_pos == (4, 0)
#        assert self.document.get_content() == '    '+TEXT_DATA
#
#    def test_Unindent_selection(self):
#        before_cursor_pos = (LAST_DOC_POS[0]+4, LAST_DOC_POS[1])
#
#        new_lines = []
#        for y, line in enumerate(self.document.get_content().split('\n')):
#            new_line = '    '+line
#            new_lines.append(new_line)
#            self.document.set_line(y, new_line)
#        self.view.cursor_pos = before_cursor_pos
#
#        self.view.selection = Selection(self.document, (0, 0), before_cursor_pos)
#
#        action = Unindent(self.view)
#        action.execute()
#        assert self.view.cursor_pos == LAST_DOC_POS
#        assert self.document.get_content() == TEXT_DATA
#
#        action.undo()
#        assert self.view.cursor_pos == before_cursor_pos
#        assert self.document.get_content() == '\n'.join(new_lines)

