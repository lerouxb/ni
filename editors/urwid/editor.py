import sys, os
import urwid
import urwid.raw_display
from pygments.token import Token
from ni.editors.base.settings import BaseSettings
from ni.editors.base.editor import Editor
from ni.editors.urwid.dialogs import *
from ni.actions.defaultactions import *
from ni.core.stack import Stack
from ni.editors.urwid.utils import make_statusline, get_urwid_lines_attrs
from ni.editors.urwid.view import UrwidView
from ni.core.document import Document, load_document

event_map = {
    'ctrl z': Undo,
    'ctrl u': Undo,
    'ctrl r': Redo,
    'ctrl n': CreateNewDocument,
    'ctrl o': OpenDocument,
    'ctrl s': SaveDocument,
    'ctrl w': CloseDocument,
    'ctrl l': ListDocuments,

    'ctrl q': ExitEditor,

    'ctrl a': SelectAll,
    'esc': CancelSelection,

    'up': MoveCursorUp,
    'down': MoveCursorDown,
    'left': MoveCursorLeft,
    'right': MoveCursorRight,
    'home': MoveCursorLineStart,
    'end': MoveCursorLineEnd,
    'page up': MoveCursorPageUp,
    'page down': MoveCursorPageDown,

    'delete': DeleteTextForward,
    'backspace': DeleteTextBackward,

    'meta ,': SwitchToPreviousDocument,
    'meta .': SwitchToNextDocument,

    'ctrl c': CopyToClipboard,
    'ctrl x': CutToClipboard,
    'ctrl v': PasteFromClipboard,
}

# These are commented under _bg_attr in urwid/escape.py:

#        'dark gray':        "100",
#        'light red':        "101",
#        'light green':        "102",
#        'yellow':        "103",
#        'light blue':        "104",
#        'light magenta':"105",
#        'light cyan':        "106",
#        'white':        "107",

palette = [
    ('plain', 'default', 'default'),
    ('error', 'white', 'dark red', 'standout'),
    ('other', 'default', 'default'),
    ('keyword', 'yellow', 'default'),
    ('name', 'default', 'default'),
    ('literal', 'brown', 'default'),
    ('operator', 'yellow', 'default'),
    ('punctuation', 'default', 'default'),
    ('comment', 'light blue', 'default'),
    ('generic', 'default', 'default'),

    ('sel_plain', 'default', 'dark blue'),
    ('sel_error', 'white', 'dark red', 'standout'),
    ('sel_other', 'default', 'dark blue'),
    ('sel_keyword', 'yellow', 'dark blue'),
    ('sel_name', 'default', 'dark blue'),
    ('sel_literal', 'brown', 'dark blue'),
    ('sel_operator', 'yellow', 'dark blue'),
    ('sel_punctuation', 'default', 'dark blue'),
    ('sel_comment', 'light blue', 'dark blue'),
    ('sel_generic', 'default', 'dark blue'),

    ('statusbar', 'black', 'light gray', 'standout'),
    ('modified', 'dark red', 'light gray', 'standout'),

    ('empty', 'light green', 'default', 'standout')
]


class UrwidTextWidget(urwid.BoxWidget):
    def __init__(self, editor):
        self.editor = editor
        super(UrwidTextWidget, self).__init__()

    def selectable(self):
        return True

    def render(self, (maxcol, maxrow), focus=False):
        view = self.editor.view
        doc = view.document

        cursory, cursorx = view.cursor_pos

        starty, startx = view.scroll_pos
        tokens = doc.tokenizer.get_normalised_tokens(starty, starty+maxrow-1)

        lines, attrs = get_urwid_lines_attrs((maxcol, maxrow), view.scroll_pos, tokens, view.selection)

        lines = [l.encode(doc.encoding) for l in lines]

        cursor_pos = (cursorx-startx, cursory-starty)
        canvas = urwid.TextCanvas(text=lines, attr=attrs, cursor=cursor_pos)

        return canvas

    def keypress(self, (maxcol, maxrow), key):
        event = key

        if event == 'enter':
            event = '\n' # TODO: this is probably not the best way if we are
                         # going to support smart indent..

        if event[:6] == 'shift ':
            event = event[6:]
            is_select = True
        else:
            is_select = False

        # get the action
        if event_map.has_key(event):
            ActionClass = event_map[event]
            if issubclass(ActionClass, MoveCursorAction):
                action = ActionClass(self.editor.view, is_select)
            else:
                action = ActionClass(self.editor.view)
        elif len(event) == 1:
            action = InsertText(self.editor.view, event)
        else:
            return

        self.editor.view.execute_action(action)


class UrwidDocumentsList(urwid.ListBox):
    def __init__(self, editor, walker):
        self.editor = editor
        super(UrwidDocumentsList, self).__init__(walker)

    def keypress(self, (maxcol, maxrow), key):
        widget, position = self.get_focus()
        if key == 'up':
            if position > 0:
                self.set_focus(position-1, 'below')
        elif key == 'down':
            if position < (len(self.body)):
                self.set_focus(position+1, 'above')
        elif key == 'enter':
            for view, pos in zip(self.editor.views, xrange(len(self.editor.views))):
                if pos == position:
                    self.editor.switch_current_view(view)

            self.editor.documents_dialog.hide()
        elif key == 'esc':
            self.editor.documents_dialog.hide()
        else:
            super(UrwidDocumentsList, self).keypress((maxcol, maxrow), key)

        return None

class UrwidEditor(Editor):
    def __init__(self, ui):
        super(UrwidEditor, self).__init__()
        path = os.path.join(os.path.expanduser('~'), '.ni', 'ni_urwid')
        self.settings = BaseSettings(path)

        self.ui = ui

        self.ui.register_palette(palette)

        # the normal "window"
        self.footer_stack = Stack()
        self.textbox = UrwidTextWidget(self)
        self.statusbar = urwid.Text(("statusbar", ""))
        self.edit_frame = urwid.Frame(self.textbox, None, self.statusbar)
        self.edit_frame.set_focus('body')

        # the document list "window"
        self.documents_listbox = UrwidDocumentsList(self, urwid.SimpleListWalker([]))
        self.documents_title = urwid.Text(("statusbar", ""))
        self.documents_frame = urwid.Frame(self.documents_listbox, None, \
          self.documents_title)
        self.documents_frame.set_focus('body')

        self.top = self.edit_frame

        self.confirm_dialog = UrwidConfirmDialog(self)
        self.open_dialog = UrwidOpenDialog(self)
        self.save_dialog = UrwidSaveDialog(self)
        #self.find_dialog = UrwidFindDialog(self)
        self.documents_dialog = UrwidListDocumentsDialog(self)

        self.must_exit = False

        self.redraw_all = True

        self.clipboard_text = ''

        # not so sure if this should be in here..
        self.new_view()

    # Implement some abstract methods defined in base:

    def _get_view(self):
        return self.view

    def _redraw_view(self, view):
        self.redraw_all = True

    def copy_to_clipboard(self, view):
        if not view.selection:
            return

        text = view.selection.get_content()
        self.clipboard_text = text

    def paste_from_clipboard(self, view):
        action = InsertText(view, self.clipboard_text)
        view.execute_action(action)

    def new_view(self, location=None):
        if location:
            document = load_document(location, self.settings)
        else:
            title = self.get_next_title()
            s = self.settings
            document = Document(encoding=s.file_encoding, linesep=s.linesep, tab_size=s.tab_size, title=title)
        view = UrwidView(self, document)
        self.views.append(view)

        # set the current view
        self.view = view

        self.queue_redraw()

        return view

    def copy_view(self):
        title = self.get_next_title()
        s = self.settings
        new_doc = Document(encoding=s.file_encoding, linesep=s.linesep, tab_size=s.tab_size, title=title)
        doc = self.view.document
        new_doc.insert(0, doc.content)
        # erm...
        new_view = GTKView(self, new_doc)
        self.views.append(new_view)
        self.switch_current_view(new_view, True)
        return new_view

    def close_view(self, view):
        if view == self.view:
            if len(self.views) > 1:
                for v in self.views:
                    if v != view:
                        self.view = v
                        break
            else:
                self.new_view()
        self.views.remove(view)

        self.queue_redraw()

    def switch_current_view(self, view):
        """Switch the active document to the one specified."""
        if not view in self.views:
            raise Exception("Invalid document.")

        # set the current view
        self.view = view
        self.queue_redraw()

    def get_textbox_dimensions(self):
        width, height = self.ui.get_cols_rows()
        return width, height-1
    textbox_dimensions = property(get_textbox_dimensions)

    def exit(self):
        self.must_exit = True


    # Define some new methods..

    def queue_redraw(self):
        """Set self.redraw_all to True which will be picked up later."""
        self.redraw_all = True

    def get_statusline(self, size):
        view = self.view
        doc = view.document

        left = doc.description

        center = None

        # position
        y, x = view.cursor_pos
        line = doc.get_line(y)
        x = tab_len(line[:x], doc.tab_size)
        x += 1
        y += 1
        position = "[%s, %s]" % (y, x)

        # mode
        if doc.tokenizer.lexer:
            mode = '('+doc.tokenizer.lexer.name+')'
        else:
            mode = ''

        # files
        num_views = len(self.views)
        files = 'File %s/%s' % (self.views.index(view)+1, num_views)

        if mode:
            right = "%s %s %s" % (position, mode, files)
        else:
            right = "%s %s" % (position, files)

        if doc.is_modified:
            leftstyle = 'modified'
        else:
            leftstyle = 'statusbar'
        return make_statusline(size, left=left, center=center, \
         right=right, leftstyle=leftstyle)

    def draw(self):
        """Draw the screen.."""

        size = self.ui.get_cols_rows()

        if self.top == self.edit_frame:
            doc = self.view.document

            if self.redraw_all:
                force = True
            else:
                force = False

            if force or doc.must_relex:
                self.textbox._invalidate()
                doc.update_tokens(self.view.scroll_pos, self.view.textbox_dimensions)

            self.statusbar.set_text(self.get_statusline(size))

            self.redraw_all = False

        elif self.top == self.documents_frame:
            line = "Select a Document (Esc to Cancel)"
            width, height = size
            line += ' '*(width-len(line))
            self.documents_title.set_text(('statusbar', line))

        canvas = self.top.render(size, focus=True)
        self.ui.draw_screen(size, canvas)

    def check_cursor(self):
        """Make sure the editor is on the screen and scroll if necessary."""

        view = self.view
        doc = view.document

        maxcol, maxrow = self.get_textbox_dimensions()
        y, x = view.cursor_pos
        topy, topx = view.scroll_pos

        # This should never happen, but for some reason it does, intermittently.
        # Cannot figure out why, so just checking the bounds here for now.
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if topx < 0:
            topx = 0
        if topy < 0:
            topy = 0

        queue_redraw = False

        if x < topx:
            topx = x
            queue_redraw = True
        if y < topy:
            topy = y
            queue_redraw = True
        if x >= (topx+maxcol):
            topx = x - maxcol + 1
            queue_redraw = True
        if y >= (topy+maxrow):
            topy = y - maxrow + 1
            queue_redraw = True

        line = doc.get_line(y)
        if len(line) < maxcol:
            topx = 0
            queue_redraw = True

        view.scroll_pos = topy, topx
        if queue_redraw:
            self.queue_redraw()

    def run(self):

        self.ui.tty_signal_keys('undefined', 'undefined', 'undefined', \
         'undefined', 'undefined')

        while True:
            size = self.ui.get_cols_rows()

            self.draw()

            events = self.ui.get_input()

            for event in events:
                if event == "window resize":
                    continue

                self.top.keypress(size, event)

                if self.must_exit:
                    return
