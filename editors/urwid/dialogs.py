import os
import urwid
from ni.core.text import pad


class BaseConfirmDialog(object):
    def __init__(self, editor):
        self.editor = editor
        self.question = ""
        self.options = ['y', 'N']
        self.default_option = 'N'
        self.callbacks = {}

    def set_question(self, question):
        self.question = question

    def set_options(self, options):
        self.options = options
        self.default_option = None
        for option in options:
            if option.upper() == option:
                self.default_option = 'N'
                break

    def set_callback(self, option, callback):
        self.callbacks[option] = callback

    def set_callbacks(self, callbacks):
        self.callbacks = callbacks

    def clear_callbacks(self):
        self.callbacks = {}

    def get_text(self):
        return self.question+' ['+('/'.join(self.options))+']'

class UrwidConfirmDialog(BaseConfirmDialog):
    def __init__(self, editor):
        super(UrwidConfirmDialog, self).__init__(editor)

    def show(self):
        self.editor.footer_stack.push(self.editor.edit_frame.get_footer())
        self.editor.edit_frame.set_footer(self)
        self.editor.edit_frame.set_focus('footer')

    def hide(self):
        previous = self.editor.footer_stack.pop()
        self.editor.edit_frame.set_footer(previous)
        if previous == self.editor.statusbar:
            self.editor.edit_frame.set_focus('body')

    # Widget stuff:

    def selectable(self):
        return True

    def get_cursor_coords(self, (maxcol,)):
        col = len(self.get_text())
        return col, 0

    def rows(self, (maxcol,), focus=False):
        return 1

    def render(self, (maxcol,), focus=False):
        text = self.get_text()
        cursor = None
        if focus:
            cursor = self.get_cursor_coords((maxcol,))

        return urwid.TextCanvas([pad(text, maxcol)], \
            attr=[[('statusbar', maxcol)]], cursor=cursor)

    def keypress(self, (maxcol,), key):
        if key in self.options or self.default_option:
            if not key in self.options and self.default_option:
                # if the key is not a valid option, make it trigger the default
                # option
                key = self.default_option
            if self.callbacks.has_key(key):
                self.callbacks[key]()
            self.hide()
        return None

class UrwidFileDialog(object):
    def __init__(self, editor):
        self.editor = editor
        self.edit = urwid.AttrWrap(urwid.Edit(), 'statusbar')

    def show(self):
        if self.editor.view.document.location:
            location = self.editor.view.document.location
            doc_dir = os.path.dirname(location) + os.path.sep
            self.edit.set_edit_text(doc_dir)
        else:
            cur_dir = os.path.realpath(os.path.curdir) + os.path.sep
            self.edit.set_edit_text(cur_dir)
        self.edit.set_edit_pos(len(self.edit.get_edit_text()))

        self.editor.footer_stack.push(self.editor.edit_frame.get_footer())
        self.editor.edit_frame.set_footer(self)
        self.editor.edit_frame.set_focus('footer')

    def hide(self):
        previous = self.editor.footer_stack.pop()
        self.editor.edit_frame.set_footer(previous)
        if previous == self.editor.statusbar:
            self.editor.edit_frame.set_focus('body')

    # Widget stuff:

    def selectable(self):
        return self.edit.selectable()

    def get_cursor_coords(self, (maxcol,)):
        return self.edit.get_cursor_coords((maxcol,))

    def rows(self, (maxcol,), focus=False):
        return self.edit.rows((maxcol,), focus)

    def render(self, (maxcol,), focus=False):
        return self.edit.render((maxcol,), focus=focus)

    def keypress(self, (maxcol,), key):
        if key == 'tab':
            actual_path = self.edit.get_edit_text()

            # immediately expand ~
            path = os.path.expanduser(actual_path)
            if path != actual_path:
                self.edit.set_edit_text(path)
                self.edit.set_edit_pos(len(path))

            if path:
                if os.path.isdir(path):
                    dirname = path
                    partial = ''
                    filenames = [filename for filename in os.listdir(dirname) if filename[0] != '.']
                else:
                    if path[-1] != os.path.sep:
                        dirname = os.path.dirname(path)
                        partial = os.path.basename(path)
                        if os.path.isdir(dirname):
                            filenames = [filename for filename in os.listdir(dirname) if filename[:len(partial)] == partial]
                        else:
                            filenames = []
                    else:
                        filenames = []

                if filenames:
                    if dirname and dirname[-1] == os.path.sep:
                        dirname = dirname[:-1]

                    if len(filenames) == 1:
                        # only one exact match, so complete it
                        text = os.path.join(dirname, filenames[0])
                        if os.path.isdir(text):
                            text += os.path.sep
                        self.edit.set_edit_text(text)
                        self.edit.set_edit_pos(len(text))

                    else:
                        # this is the difficult bit... if we can match a common
                        # prefix, then we should expand to that
                        common = ''
                        check = partial
                        found = True
                        while found:
                            for filename in filenames:
                                if not filename[:len(check)] == check:
                                    found = False
                            if found:
                                common = check
                                if len(filenames[0]) > len(check):
                                    check = filenames[0][:len(check)+1]

                        if common:
                            text = os.path.join(dirname, common)
                            if os.path.isdir(text):
                                text += os.path.sep
                            self.edit.set_edit_text(text)
                            self.edit.set_edit_pos(len(text))

        elif key == 'enter':
            self.choose()

        elif key == 'esc':
            self.hide()

        else:
            self.edit.keypress((maxcol,), key)

        return None

class UrwidOpenDialog(UrwidFileDialog):
    def __init__(self, editor):
        super(UrwidOpenDialog, self).__init__(editor)
        self.edit.set_caption('Open: ')

    def choose(self):
        path = os.path.expanduser(self.edit.get_edit_text())
        if os.path.isfile(path):
            self.editor.new_view(path)
        self.hide()

class UrwidSaveDialog(UrwidFileDialog):
    def __init__(self, editor):
        super(UrwidSaveDialog, self).__init__(editor)
        self.edit.set_caption('Save: ')

    def choose(self):
        try:
            path = os.path.expanduser(self.edit.get_edit_text())
            dirname = os.path.dirname(path)
            if os.path.isdir(dirname):
                def save():
                    doc = self.editor.view.document
                    doc.save(path)
                    self.hide()

                def hide():
                    self.hide()

                if not os.path.exists(path):
                    # new file
                    save()

                elif os.path.isfile(path):
                    # overwrite existing file
                    dialog = self.editor.confirm_dialog
                    question = "File exists. Overwrite?"
                    dialog.set_question(question)
                    dialog.set_options(['y', 'N'])
                    dialog.clear_callbacks()
                    dialog.set_callback("y", save)
                    dialog.set_callback("N", hide)
                    dialog.show()

                else:
                    pass
        finally:
            if self.editor.edit_frame.get_footer() == self:
                self.hide()

class UrwidListDocumentsDialog(object):
    def __init__(self, editor):
        self.editor = editor

    def show(self):
        from ni.editors.urwid.editor import UrwidDocumentsList

        widgets = [urwid.AttrWrap(urwid.Text(v.document.description), None, 'sel_plain') \
          for v in self.editor.views]

        self.editor.documents_listbox = UrwidDocumentsList(self.editor, \
          urwid.SimpleListWalker(widgets))

        self.editor.documents_frame.set_body(self.editor.documents_listbox)

        current_document = self.editor.view.document
        for view, pos in zip(self.editor.views, \
          xrange(len(self.editor.views))):
            if view.document == current_document:
                self.editor.documents_listbox.set_focus(pos)

        self.editor.top = self.editor.documents_frame
        self.editor.queue_redraw()

    def hide(self):
        self.editor.top = self.editor.edit_frame
        self.editor.queue_redraw()

