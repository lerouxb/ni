from ni.core.selection import Selection
from ni.actions.base import *
from ni.core.text import get_word_range, char_pos_to_tab_pos, \
  tab_pos_to_char_pos, tab_len
from ni.core.document import InsertDelta, DeleteDelta


class Undo(Action):
    """
    Undo last action
    """

    def execute(self):
        self.editor.undo(self.view)


class Redo(Action):
    """
    Redo last undo action
    """

    def execute(self):
        self.editor.redo(self.view)

class SwitchToRecentDocument(Action):
    """
    Switch to most recent document
    """

    def execute(self):
        if self.editor.previous_view:
            self.editor.switch_current_view(self.editor.previous_view)

class SwitchToPreviousDocument(Action):
    """
    Switch to previous document
    """

    def execute(self):
        if not len(self.editor.views):
            return

        self.editor.switch_to_previous_view()


class SwitchToNextDocument(Action):
    """
    Switch to next document
    """

    def execute(self):
        if not len(self.editor.views):
            return

        self.editor.switch_to_next_view()


class CreateNewDocument(Action):
    """
    Create a new document.
    """

    def execute(self):
        self.editor.new_view()


class CloseDocument(Action):
    """
    Close the current document.
    """

    def execute(self):
        self.editor.close_view()


class OpenDocument(Action):
    """
    Show the open dialog.
    """

    def execute(self):
        self.editor.open_dialog.show()


class SwitchDocument(Action):
    """
    Show the switch document dialog.
    """

    def execute(self):
        self.editor.switch_dialog.show()


class SaveDocument(Action):
    """
    Save the open document
    """

    def execute(self):
        doc = self.view.document
        if doc.location:
            doc.save()
            self.view.invalidate()
        else:
            self.editor.save_dialog.show()

class SaveDocumentAs(Action):
    """
    Save the open document as a new file
    """

    def execute(self):
        new_view = self.editor.copy_view()
        # the new view will already be the active one
        self.editor.save_dialog.show()

class ListDocuments(Action):
    """
    Show the document list dialog.
    """

    def execute(self):
        self.editor.documents_dialog.show()

class GoToLine(Action):
    """

    """

    def execute(self):
        self.editor.goto_dialog.show()

class AddWorkspace(Action):
    """

    """

    def execute(self):
        self.editor.add_workspace_dialog.show()

class EditWorkspace(Action):
    """

    """

    def execute(self):
        self.editor.edit_workspace_dialog.show()

class ClearWorkspaceCache(Action):
    """
    
    """
    
    def execute(self):        
        self.editor.switch_dialog.sync_workspace()
        self.editor.find_dialog.sync_workspace()

class Preferences(Action):
    """

    """

    def execute(self):
        self.editor.preferences_dialog.show()

class FindorReplace(Action):
    """

    """

    def execute(self):
        self.editor.find_dialog.show()

class ExitEditor(Action):
    """
    Show the confirm exit dialog.
    """

    def execute(self):
        self.editor.exit()


class ToggleSidebar(Action):
    """
    Show/Hide the document tree thing.
    """

    def execute(self):
        self.editor.toggle_sidebar()


# TODO: rename to ToggleGutter
class ToggleLineNumbers(Action):
    """
    Show/Hide the gutter.
    """

    def execute(self):
        self.editor.toggle_gutter()


class ToggleStatusbar(Action):
    """
    Show/Hide the statusbar.
    """

    def execute(self):
        self.editor.toggle_statusbar()


# TODO: rename to ToggleMargin
class ToggleRightMargin(Action):
    """
    Show/Hide the 80 char margin.
    """

    def execute(self):
        self.editor.toggle_margin()

class SelectWord(Action):
    """
    Select the word around the cursor.
    """

    def execute(self):
        view = self.view
        doc = view.document
        y, x = view.cursor_pos

        if view.selection:
            # typically select word only occurs when you double-click and
            # click will probably clear the selection, but you never know...
            view.selection = None
            view.invalidate()

        line = doc.get_line(y)
        span = get_word_range(line, x)
        if span:
            start_index = span[0]
            end_index = span[1]
            start_offset = doc.cursor_pos_to_offset((y, start_index))
            end_offset = doc.cursor_pos_to_offset((y, end_index))
            view.selection = Selection(doc, start_offset, end_offset)
            view.invalidate()
            view.last_x_pos = char_pos_to_tab_pos(line,
                                                  end_index,
                                                  doc.tab_size)
            view.cursor_pos = (y, end_index)

class SelectAll(Action):
    """
    Select the entire document.
    """

    def execute(self):
        view = self.view
        doc = view.document
        view.selection = Selection(doc, 0, len(doc.content))
        view.invalidate()

class CancelSelection(Action):
    """
    If a selection exists, remove it.
    """

    def execute(self):
        view = self.view
        if view.selection:
            view.selection = None
            view.invalidate()


class MoveCursor(MoveCursorAction):
    def __init__(self, view, pos, select=False):
        super(MoveCursor, self).__init__(view)
        self.newpos = pos

    def move(self):
        view = self.view
        doc = view.document
        y, x = self.newpos

        # we're explicitely setting x, so update last_x_pos
        view.last_x_pos = x

        # try and set where we clicked, otherwise set x to the end of the line
        line = doc.get_line(y)
        if tab_len(line, doc.tab_size) > view.last_x_pos:
            x = tab_pos_to_char_pos(line, view.last_x_pos, doc.tab_size)
        else:
            x = len(line)

        view.cursor_pos = (y, x)

class MoveCursorUp(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        y, x = view.cursor_pos
        
        if y == 0:
            return
        
        y -= 1
        line = doc.get_line(y)
        if tab_len(line, doc.tab_size) > view.last_x_pos:
            x = tab_pos_to_char_pos(line, view.last_x_pos, doc.tab_size)
        else:
            x = len(line)

        view.cursor_pos = (y, x)

class MoveCursorDown(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        y, x = view.cursor_pos

        if y == doc.num_lines - 1:
           return

        y += 1
        line = doc.get_line(y)
        if tab_len(line, doc.tab_size) > view.last_x_pos:
            x = tab_pos_to_char_pos(line, view.last_x_pos, doc.tab_size)
        else:
            x = len(line)

        view.cursor_pos = (y, x)

class MoveCursorLeft(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        #y, x = prev_pos(doc, view.cursor_pos)
        y, x = view.cursor_pos
        if x > 0:
            x -= 1
            line = doc.get_line(y)
        elif y > 0:
            y -= 1
            line = doc.get_line(y)
            x = len(line)
        else:
            return
        
        view.cursor_pos = (y, x)
        view.last_x_pos = char_pos_to_tab_pos(line, x, doc.tab_size)

class MoveCursorRight(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        #x, y = next_pos(doc, view.cursor_pos)
        y, x = view.cursor_pos
        line = doc.get_line(y)
        if x < len(line):
            x += 1
        elif y < doc.num_lines-1:
            y += 1
            x = 0
            line = doc.get_line(y)
        else:
            return
        
        view.cursor_pos = (y, x)        
        view.last_x_pos = char_pos_to_tab_pos(line, x, doc.tab_size)

class MoveCursorWordLeft(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        y, x = view.cursor_pos

        if x == 0:
            if y > 0:
                line = doc.get_line(y-1)
                lx = len(line)
                view.cursor_pos = (y-1, lx)
                view.last_x_pos = char_pos_to_tab_pos(line, lx, doc.tab_size)

        else:
            line = doc.get_line(y)
            span = get_word_range(line, x-1)
            if span:
                view.cursor_pos = (y, span[0])
                view.last_x_pos = char_pos_to_tab_pos(line,
                                                      span[0],
                                                      doc.tab_size)

class MoveCursorWordRight(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        y, x = view.cursor_pos

        if x == len(doc.get_line(y)):
            last_line = doc.num_lines - 1
            if y < last_line:
                view.cursor_pos = (y+1, 0)
                view.last_x_pos = 0
        else:
            line = doc.get_line(y)
            span = get_word_range(line, x)
            if span:
                view.cursor_pos = (y, span[1])
                view.last_x_pos = char_pos_to_tab_pos(line,
                                                      span[1],
                                                      doc.tab_size)

class MoveCursorLineStart(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        y, x = view.cursor_pos
        line = doc.get_line(y)

        line_start = len(line) - len(line.lstrip())

        # toggle between first non-whitespace character and actual start
        if x == line_start:
            x = 0
        else:
            x = line_start

        view.cursor_pos = (y, x)
        view.last_x_pos = char_pos_to_tab_pos(line, x, doc.tab_size)

class MoveCursorLineEnd(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        y, x = view.cursor_pos
        line = doc.get_line(y)

        line_end = len(line.rstrip())

        if x == line_end:
            x = len(line)
        else:
            x = line_end

        view.cursor_pos = (y, x)
        view.last_x_pos = char_pos_to_tab_pos(line, x, doc.tab_size)

class MoveCursorStart(MoveCursorAction):
    def move(self):
        view = self.view
        view.cursor_pos = (0, 0)
        view.last_x_pos = 0

class MoveCursorEnd(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document
        y = doc.num_lines - 1
        line = doc.get_line(y)
        x = len(line)
        view.cursor_pos = (y, x)
        view.last_x_pos = char_pos_to_tab_pos(line, x, doc.tab_size)

class MoveCursorPageUp(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document

        maxcol, maxrow = view.page_size

        y, x = view.cursor_pos
        y -= maxrow
        if y < 0:
            x = 0
            y = 0
        else:
            linelen = len(doc.get_line(y))
            if x > linelen:
                x = linelen

        view.cursor_pos = (y, x)
        
        scrolly, scrollx = view.scroll_pos
        scrolly -= maxrow
        if scrolly < 0:
            scrollx = 0
            scrolly = 0

        view.scroll_pos = (scrolly, scrollx)

class MoveCursorPageDown(MoveCursorAction):
    def move(self):
        view = self.view
        doc = view.document

        maxcol, maxrow = view.page_size
        lastline = doc.num_lines - 1

        y, x = view.cursor_pos
        y += maxrow
        if y > lastline:
            x = len(doc.get_line(lastline))
            y = lastline
                    
        linelen = len(doc.get_line(y))
        if x > linelen:
            x = linelen

        view.cursor_pos = (y, x)

        scrolly, scrollx = view.scroll_pos
        scrolly += maxrow
        if scrolly > lastline:
            scrolly = lastline            

        view.scroll_pos = (scrolly, scrollx)

class InsertText(EditAction):
    """
    Insert some text into the document.
    """

    def __init__(self, view, text):
        super(InsertText, self).__init__(view)
        self.text = text

    def do(self):
        view = self.view
        doc = view.document

        # if there's a selection when the user types, it should be deleted
        # first so that we "override" it
        if view.selection:
            self.delete_selection()

        offset = doc.cursor_pos_to_offset(view.cursor_pos)
                
        d = InsertDelta(doc, offset, self.text)
        d.do()
        self.deltas.append(d)
        
        offset += tab_len(self.text, doc.tab_size)
        view.cursor_pos = doc.offset_to_cursor_pos(offset)        

class CopyToClipboard(Action):
    """
    Copies the selection to the clipboard
    """

    def execute(self):
        # Just pass it on to the editor object, because the way the clipboard
        # works is too "frontend"-specific.
        self.editor.copy_to_clipboard(self.view)


class PasteFromClipboard(Action):
    """
    Paste contents of clipboard.
    """

    def execute(self):
        # Just pass it on to the editor object, because the way the clipboard
        # works is too "frontend"-specific.
        # Most likely there will be a callback mechanism and then it can just
        # turn into a normal InsertAction
        self.editor.paste_from_clipboard(self.view)


class CutToClipboard(EditAction):
    """
    Copies the selection to the clipboard and deletes it.
    """

    def do(self):
        view = self.view
        doc = view.document

        if view.selection:
            # the way clipboards work is frontend-specific, so just pass the
            # copy part on
            self.editor.copy_to_clipboard(view)

            self.delete_selection()


class DeleteSelection(EditAction):
    """
    Delete the selection if there is one.
    """

    def do(self):
        if self.view.selection:
            self.delete_selection()

class DeleteTextForward(EditAction):
    """
    Delete the selection or the next character from the document.
    """
    
    def do(self):
        view = self.view
        doc = view.document
        
        if view.selection:
            self.delete_selection()
        
        else:
            offset = doc.cursor_pos_to_offset(view.cursor_pos)
            
            # if we're at the end of the file, do nothing
            if offset >= len(doc.content)-1:
                return
            
            # delete the character under the cursor            
            d = DeleteDelta(doc, offset, 1)
            d.do()
            self.deltas.append(d)

class DeleteTextBackward(EditAction):
    """
    Delete the selection or the previous character from the document.
    """
    
    def do(self):
        view = self.view
        doc = view.document
        
        if view.selection:
            self.delete_selection()
        
        else:
            offset = doc.cursor_pos_to_offset(view.cursor_pos)
            
            # if we're at the start of the file, do nothing
            if offset <= 0:
                return
            
            # delete the character before the cursor            
            d = DeleteDelta(doc, offset-1, 1)
            d.do()
            self.deltas.append(d)
            
            view.cursor_pos = doc.offset_to_cursor_pos(offset-1)

class Indent(EditAction):
    """
    Indent the selection or current line.
    """
    
    def do(self):
        view = self.view
        doc = view.document
        settings = self.editor.settings
        
        if view.selection:
            # indent the selection
            selection = view.selection.get_normalised()
            
            # selections that grow upwards need slightly different 
            # attention to selections that grow downwards
            if selection.start == view.selection.start:
                selection_direction = "down"
            else:
                selection_direction = "up"
            
            # convert the offsets and unpack
            start_pos = doc.offset_to_cursor_pos(selection.start)
            start_y, start_x = start_pos
            end_pos = doc.offset_to_cursor_pos(selection.end)
            end_y, end_x = end_pos
            
            # add the actual insert deltas
            for i in xrange(start_y, end_y+1):
                offset = doc.cursor_pos_to_offset((i, 0))
                d = InsertDelta(doc, offset, u" "*settings.indent_width)
                d.do()
                self.deltas.append(d)
            
            # Adjust the start and end positions of the selection.
            # The checks on start_x and end_x are there to keep the selection 
            # anchored to the start of a line if it started or ended at
            # the start (for no reason other than this is what jedit does)
            num_lines = end_y-start_y+1
            if selection_direction == "down":                
                if start_x != 0:
                    view.selection.start += settings.indent_width
            else:
                if start_x != 0:
                    view.selection.end += settings.indent_width
            if selection_direction == "down":
                n = num_lines
                if end_x == 0:
                    n -= 1
                view.selection.end += (settings.indent_width*n)
                view.cursor_pos = doc.offset_to_cursor_pos(view.selection.end)
            else:
                n = num_lines
                if end_x == 0:
                    n -= 1
                view.selection.start += (settings.indent_width*n)
                view.cursor_pos = doc.offset_to_cursor_pos(view.selection.start)
            
        else:            
            # indent only the current line
            y, x = view.cursor_pos
            offset = doc.cursor_pos_to_offset((y, 0))
            d = InsertDelta(doc, offset, u" "*settings.indent_width)
            d.do()
            self.deltas.append(d)
            
            # only move the cursor if we're not at the start of the line
            # (this is just to clone jedit's behavior)
            if x != 0:
                view.cursor_pos = (y, x+settings.indent_width)

class Unindent(EditAction):
    """
    Unindent the selection or current line.
    """

    def do(self):
        view = self.view
        doc = view.document
        settings = self.editor.settings
        
        if view.selection:
            # unindent the selection
            selection = view.selection.get_normalised()
            
            # selections that grow upwards need slightly different 
            # attention to selections that grow downwards
            if selection.start == view.selection.start:
                selection_direction = "down"
            else:
                selection_direction = "up"
            
            # convert the offsets and unpack
            start_pos = doc.offset_to_cursor_pos(selection.start)
            start_y, start_x = start_pos
            end_pos = doc.offset_to_cursor_pos(selection.end)
            end_y, end_x = end_pos
            
            # add the delete deltas
            spaces_per_line = []
            for y in xrange(start_y, end_y+1):
                line = doc.get_line(y).replace('\t', u' '*settings.tab_size)
                oline = line
                for i in xrange(settings.indent_width):
                    if line and line[0] == u' ':
                        line = line[1:]
                    else:
                        break
                num_spaces = len(oline)-len(line)
                spaces_per_line.append(num_spaces)
                if num_spaces:
                    offset = doc.cursor_pos_to_offset((y, 0))
                    d = DeleteDelta(doc, offset, num_spaces)
                    d.do()
                    self.deltas.append(d)
             
            if selection_direction == "down":
                start_x -= spaces_per_line[0]
                if start_x < 0:
                    start_x = 0
                view.selection.start = doc.cursor_pos_to_offset(
                    (start_y, start_x))                
                end_x -= spaces_per_line[-1]
                if end_x < 0:
                    end_x = 0
                view.selection.end = doc.cursor_pos_to_offset((end_y, end_x))
            else:
                start_x -= spaces_per_line[-1]
                if start_x < 0:
                    start_x = 0
                view.selection.start = doc.cursor_pos_to_offset(
                    (start_y, start_x))                
                end_x -= spaces_per_line[0]
                if end_x < 0:
                    end_x = 0
                view.selection.end = doc.cursor_pos_to_offset((end_y, end_x))
            
        else:
            # unindent only the current line
            y, x = view.cursor_pos 
            line = doc.get_line(y).replace('\t', u' '*settings.tab_size)
            oline = line
            for i in xrange(settings.indent_width):
                if line and line[0] == u' ':
                    line = line[1:]
                else:
                    break
            num_spaces = len(oline)-len(line)
            if num_spaces:
                offset = doc.cursor_pos_to_offset((y, 0))
                d = DeleteDelta(doc, offset, num_spaces)
                d.do()
                self.deltas.append(d)
                x -= num_spaces
                if x < 0:
                    x = 0
                view.cursor_pos = (y, x)

class ToggleHashComment(ToggleComment):
    def __init__(self, view):        
        super(ToggleHashComment, self).__init__(view, u"#")

class ToggleSlashComment(ToggleComment):
    def __init__(self, view):        
        super(ToggleSlashComment, self).__init__(view, u"//")

class ToggleDashComment(ToggleComment):
    def __init__(self, view):        
        super(ToggleDashComment, self).__init__(view, u"--")

class BlockComment(EditAction):
    def do(self):
        view = self.view
        doc = view.document
        settings = self.editor.settings
        
        # this only works on selections
        if not view.selection:
            return
        
        selection = view.selection.get_normalised()
        d = InsertDelta(doc, selection.start, u"/*")
        d.do()
        self.deltas.append(d)
        d = InsertDelta(doc, selection.end+2, u"*/")
        d.do()
        self.deltas.append(d)
        
        view.cursor_pos = doc.offset_to_cursor_pos(selection.end+4)
        view.selection = None
