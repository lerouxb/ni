from ni.core.selection import Selection
from ni.core.text import char_pos_to_tab_pos
from ni.core.document import InsertDelta, DeleteDelta


class Action(object):
    """Base class for all view actions."""

    def __init__(self, view):
        self.grouped = False
        self.editor = view.editor
        self.view = view

    def execute(self):
        raise NotImplementedError

class MoveCursorAction(Action):
    """Base class for all actions that involve moving the cursor around."""
    
    def __init__(self, view, is_select=False):
        super(MoveCursorAction, self).__init__(view)
        self.is_select = is_select

    def execute(self):
        view = self.view
        doc = view.document

        original_position = view.cursor_pos
        original_scroll = view.scroll_pos

        self.move()

        if original_position != view.cursor_pos or \
           original_scroll != view.scroll_pos:
            view.invalidate()
            if self.is_select:
                if view.selection:
                    end_offset = doc.cursor_pos_to_offset(view.cursor_pos)
                    view.selection.end = end_offset
                else:                    
                    start_offset = doc.cursor_pos_to_offset(original_position)
                    end_offset = doc.cursor_pos_to_offset(view.cursor_pos)
                    #print original_position, view.cursor_pos, start_offset, end_offset
                    view.selection = Selection(doc, start_offset, end_offset)

    def move(self):
        raise NotImplementedError

class EditAction(Action):
    """Base class for all undoable actions."""

    def __init__(self, view):
        super(EditAction, self).__init__(view)
        self.before_cursor_pos = None
        self.before_last_x_pos = None
        self.before_scroll_pos = None

        self.after_cursor_pos = None
        self.after_last_x_pos = None
        self.after_scroll_pos = None

        self.deltas = []

        self.is_executed = False

    def execute(self):
        """
        Save positions so that we can return later and call self.do().
        """

        self.is_executed = True

        view = self.view

        # for undo purposes
        self.before_cursor_pos = view.cursor_pos
        self.before_last_x_pos = view.last_x_pos
        self.before_scroll_pos = view.scroll_pos

        self.do()

        # recalculate last_x_pos based on where the cursor is now
        doc = view.document
        y, x = view.cursor_pos
        line = doc.get_line(y)
        view.last_x_pos = char_pos_to_tab_pos(line, x, doc.tab_size)

        # for redo purposes
        self.after_cursor_pos = view.cursor_pos
        self.after_last_x_pos = view.last_x_pos
        self.after_scroll_pos = view.scroll_pos

        view.invalidate()

    def delete_selection(self):
        """
        Common code for deleting a selection used by many edit actions.
        """

        view = self.view
        doc = view.document

        # delete the selection
        selection = view.selection.get_normalised()
        d = DeleteDelta(doc, selection.start, selection.end-selection.start+1)
        d.do()
        self.deltas.append(d)
        view.selection = None

        # move the cursor (insert point) to the start of where the selection
        # was before we deleted it
        view.cursor_pos = doc.offset_to_cursor_pos(selection.start)

    def do(self):
        """
        Subclasses should implement this.
        """

        raise NotImplementedError

    def undo(self):
        if not self.is_executed:
            raise RuntimeError("Not executed")

        for d in reversed(self.deltas):
            d.undo()

        # reset the cursor and scroll positions to where it was
        self.view.cursor_pos = self.before_cursor_pos
        self.view.last_x_pos = self.before_last_x_pos
        self.view.scroll_pos = self.before_scroll_pos

        self.view.invalidate()

    def redo(self):
        if not self.is_executed:
            raise RuntimeError("Not executed")

        for d in self.deltas:
            d.do()

        # reset the cursor and scroll positions to where it was
        self.view.cursor_pos = self.after_cursor_pos
        self.view.last_x_pos = self.after_last_x_pos
        self.view.scroll_pos = self.after_scroll_pos

        self.view.invalidate()
        
class ToggleComment(EditAction):
    def __init__(self, view, comment_string):
        self.comment_string = comment_string
        super(ToggleComment, self).__init__(view)
        
    def do(self):
        view = self.view
        doc = view.document
        settings = self.editor.settings
        
        if view.selection:            
            selection = view.selection.get_normalised()
            from_line = doc.offset_to_cursor_pos(selection.start)[0]
            to_line = doc.offset_to_cursor_pos(selection.end)[0]
        else:
            from_line = view.cursor_pos[0]
            to_line = from_line
        
        for y in xrange(from_line, to_line+1):
            line = doc.get_line(y)
            offset = doc.cursor_pos_to_offset((y, 0))
            if line[:len(self.comment_string)] == self.comment_string:
                d = DeleteDelta(doc, offset, len(self.comment_string))
            else:
                d = InsertDelta(doc, offset, self.comment_string)
            d.do()
            self.deltas.append(d)
        
        # move the cursor if necessary
        y, x = view.cursor_pos
        line = doc.get_line(y)
        if line[:len(self.comment_string)] == self.comment_string:
            # we added comment_string, so increase cursor pos
            if x != 0:
                x += len(self.comment_string)
                if x > len(line):
                    x = len(line)
                view.cursor_pos = (y, x)
        else:            
            # we removed comment_string, so decrease cursor pos
            x -= len(self.comment_string)
            if x < 0:
                x = 0
            view.cursor_pos = (y, x)
        
        # not sure how best to grow/shrink the selection right now, 
        # so just destroying it for now
        view.selection = None
            
