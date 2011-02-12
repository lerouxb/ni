from ni.core.selection import Selection


# Basically this is just an interface being declared. Actual editors must
# inherit from ni.editors.base.editor.Editor, implement these methods and
# probably extend things quite a bit in order to be useful.

def actions_are_grouped(x, y):
    if x == y:
        return True
    return isinstance(x, type(y)) and x.grouped and x.grouped == y.grouped

class Editor(object):
    def __init__(self):
        self.previous_view = None
        self.views = []
        self.searches = []
        self.search = None

        self.next_untitled_number = 1

        self.workspace = None
        self.workspaces = []

        # why is this here again?
        self.confirm_dialog = None
        self.open_dialog = None
        self.goto_dialog = None
        self.switch_dialog = None
        self.add_workspace_dialog = None
        self.edit_workspace_dialog = None
        self.preferences_dialog = None
        self.find_dialog = None

    def exit(self):
        """Cause the editor to exit asap."""

        raise NotImplementedError()

    def new_view(self, location=None):
        """Create a new document, open a new document or create a new view on an
        existing document."""

        raise NotImplementedError()

    def copy_view(self):
        """Make a copy of the view and return it."""

        raise NotImplementedError()

    def close_view(self, view):
        """Close the specified view."""

        raise NotImplementedError()

    def switch_current_view(self, view):
        """Switch the active document to the one specified."""

        raise NotImplementedError()

    def switch_to_previous_view(self):
        # this is quite dumb and will probably always be overridden in an
        # actual editor
        pos = self.views.index(self._get_view())
        if pos >= 1:
            pos -= 1
        else:
            pos = len(self.views)-1
        self.switch_current_view(self.views[pos])

    def switch_to_next_view(self):
        # this is quite dumb and will probably always be overridden in an
        # actual editor
        pos = self.views.index(self._get_view())
        if pos < len(self.views)-1:
            pos += 1
        else:
            pos = 1
        self.switch_current_view(self.views[pos])

    # _get_view and _redraw_view exists because where the actual current view
    # gets stored and how it gets redrawn depends on the actual editor. This is
    # just here so that we can share some more code in the base class without
    # the base class having to know about those details.

    def _get_view(self):
        """used by Editor to get the current view."""

        raise NotImplementedError()

    def _redraw_view(self, view):
        """used by Editor to redraw the specified view."""

        raise NotImplementedError()


    def copy_to_clipboard(self, view):
        """Copy the specified view's selection to the clipboard."""

        raise NotImplementedError()

    def paste_from_clipboard(self, view):
        """Paste the clipboard's contents into the specified view."""

        raise NotImplementedError()


    def cancel_search(self, search):
        for s in self.searches:
            if s == search:
                s.detach()
                break

        self.searches.remove(search)

        if self.search == search:
            self.search = None

    # In most cases the following code should be enough to implement undo/redo,
    # but an actual editor can extend this if it needs to do extra stuff

    def undo(self, view):
        """Undo the current document's previous action."""

        last_action = view.document.undo_stack.last()
        if last_action:
            view.selection = None
            action = last_action
            while actions_are_grouped(action, last_action):
                view.document.undo_stack.pop() # remove
                action.undo()
                view.document.redo_stack.push(action)
                action = view.document.undo_stack.last()
            self._redraw_view(view)

    def redo(self, view):
        """Undo the current document's previously undone action."""

        last_action = view.document.redo_stack.last()
        if last_action:
            view.selection = None
            action = last_action
            while actions_are_grouped(action, last_action):
                view.document.redo_stack.pop() # remove
                action.redo()
                view.document.undo_stack.push(action)
                action = view.document.redo_stack.last()
            self._redraw_view(view)


    def get_next_title(self):
        """
        Return a unique string to use as the title for the next unsaved
        document.
        """

        title = "UNTITLED " + str(self.next_untitled_number)
        self.next_untitled_number += 1
        return title

