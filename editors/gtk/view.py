from ni.editors.base.view import View
from ni.editors.gtk.utils import get_gtk_colours
from ni.actions.base import EditAction


class GTKView(View):
    def __init__(self, editor, document):
        super(GTKView, self).__init__(editor, document)
        self.textarea = editor.textarea
        self.is_valid = False
        self.brackets = None
        self.just_switched = False

    def set_colours(self):
        colourscheme = self.textarea.editor.colourscheme
        if self.document.tokenizer.lexer:
            mode = self.document.tokenizer.lexer.name
        else:
            mode = 'plain'
        self._colours = get_gtk_colours(self.textarea.drawingarea,
                                        colourscheme, mode)
        self.textarea.pl = None

    def get_colours(self):
        if not hasattr(self, '_colours'):
            self.set_colours()
        return self._colours
    colours = property(get_colours)

    def _get_textbox_dimensions(self):
        return self.textarea.textbox_dimensions
    textbox_dimensions = property(_get_textbox_dimensions)

    def _get_page_size(self):
        return self.textarea.page_size
    page_size = property(_get_page_size)

    def invalidate(self):
        self.is_valid = False # this gets checked later

    def sync_selection(self):
        """
        Enable/Disable selection controls.
        """
        
        if self.selection:
            sensitive = True            
        else:
            sensitive = False            
        self.editor.selection_actiongroup.set_sensitive(sensitive)

    def execute_action(self, action):
        old_scroll_pos = self.scroll_pos
        old_view = self.textarea.view
        
        # don't allow edit actions if we're performing a non-interruptable
        # search
        if isinstance(action, EditAction):
            if self.editor.search and not self.editor.search.can_interrupt():
                return

        super(GTKView, self).execute_action(action)
        
        # if there are undoable actions, then the undo action has to be enabled
        # if there are redoable actions, then the redo action has to be enabled
        # otherwise we might have to disable either of those
        self.textarea.editor.update_undoredo()

        # if we didn't invalidate the view for whatever reason, then we short
        # circuit here as an optimisation. In practice we'll usually invalidate
        # the view, though.
        if self.is_valid:
            return
            
        self.is_valid = True
        if self.scroll_pos != old_scroll_pos:
            # we might have scrolled, so we have to copy the positions
            # across to the scrollbars
            self.textarea.sync_scroll_pos()
            # the size of the longest line might have changed or the number
            # of lines, so we have to re-calculate the scrollbars' limits
            # and things
            self.textarea.adjust_adjustments()

        # for now, whenever we perform an action, recalculate brackets
        # None means we need to re-evaluate (for now)
        self.brackets = None

        # By setting cursor visible to True, it stops annoying flicker when
        # the cursor gets moved around
        self.textarea.is_cursor_visible = True

        if isinstance(action, EditAction):
            # edit actions always change the document, so the pango layout
            # is invalid
            self.textarea.pl = None

            # notify the relevant searches
            for search in self.editor.searches:
                # removed because ties things too tightly
                #y = self.document.relex_from[1]
                #search.notify_change(self.document.location, y)
                search.notify_change(self.document.location)

            if self.editor.search:
                search.interrupt()
                search.incr_update()

        if self.scroll_pos != old_scroll_pos or \
           self.textarea.view != old_view:
            # the pango layout is invalid because we scrolled or switched
            # views
            self.textarea.pl = None

        # we might have made a new selection where we didn't have one 
        # before or we might have removed the selection. So the selection
        # controls/actions might have to be enabled or disabled
        self.sync_selection()
        
        # trigger a redraw because the view got invalidated
        self.textarea.redraw()
        
