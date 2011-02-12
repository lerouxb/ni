import os
import re
import sys
import gtk
import gtk.glade
import gobject
from ni.core.text import slugify
from ni.core.workspace import Workspace
from ni.editors.gtk.settings import GLADE_DIR


def add_text_column(treeview, label, num):
    column = gtk.TreeViewColumn(label)
    cell = gtk.CellRendererText()
    column.pack_start(cell)
    column.add_attribute(cell, 'text', num)
    treeview.append_column(column)

class GtkWorkspaceDialog(object):
    def __init__(self, editor):
        self.editor = editor

    def common_init(self, g):
        self.window = g.get_widget('window')
        self.window.set_transient_for(self.editor.window)
        self.window.set_resizable(True)
        self.window.set_default_size(512, 384)

        self.edit_exclude_dialog = GtkEditExcludeDialog(self.editor,
                                                        self.window)
        self.edit_filter_dialog = GtkEditFilterDialog(self.editor,
                                                      self.window)

        # set up references:

        self.notebook = g.get_widget('notebook')
        self.name_entry = g.get_widget('name_entry')
        self.dir_entry = g.get_widget('dir_entry')
        self.browse_button = g.get_widget('browse_button')
        self.cancel_button = g.get_widget('cancel_button')

        self.glob_exclude_treeview = g.get_widget('glob_exclude_treeview')
        self.glob_exclude_entry = g.get_widget('glob_exclude_entry')
        self.glob_exclude_add_button = g.get_widget('glob_exclude_add_button')
        self.regex_exclude_treeview = g.get_widget('regex_exclude_treeview')
        self.regex_exclude_entry = g.get_widget('regex_exclude_entry')
        self.regex_exclude_add_button = g.get_widget('regex_exclude_add_button')

        self.glob_filter_treeview = g.get_widget('glob_filter_treeview')
        self.glob_filter_name_entry = g.get_widget('glob_filter_name_entry')
        self.glob_filter_pattern_entry = g.get_widget('glob_filter_pattern_entry')
        self.glob_filter_add_button = g.get_widget('glob_filter_add_button')
        self.regex_filter_treeview = g.get_widget('regex_filter_treeview')
        self.regex_filter_name_entry = g.get_widget('regex_filter_name_entry')
        self.regex_filter_pattern_entry = g.get_widget('regex_filter_pattern_entry')
        self.regex_filter_add_button = g.get_widget('regex_filter_add_button')

        # set up liststores:

        self.glob_exclude_liststore = gtk.ListStore(str)
        self.glob_exclude_treeview.set_model(self.glob_exclude_liststore)
        add_text_column(self.glob_exclude_treeview, 'GLOB', 0)
        self.glob_exclude_treeview.set_headers_visible(False)
        self.glob_exclude_treeview_sel = self.glob_exclude_treeview.get_selection()
        self.glob_exclude_treeview_sel.set_mode(gtk.SELECTION_SINGLE)

        self.regex_exclude_liststore = gtk.ListStore(str)
        self.regex_exclude_treeview.set_model(self.regex_exclude_liststore)
        add_text_column(self.regex_exclude_treeview, 'Regular Expression', 0)
        self.regex_exclude_treeview.set_headers_visible(False)
        self.regex_exclude_treeview_sel = self.regex_exclude_treeview.get_selection()
        self.regex_exclude_treeview_sel.set_mode(gtk.SELECTION_SINGLE)

        self.glob_filter_liststore = gtk.ListStore(str, str)
        self.glob_filter_treeview.set_model(self.glob_filter_liststore)
        add_text_column(self.glob_filter_treeview, 'Name', 0)
        add_text_column(self.glob_filter_treeview, 'GLOB', 1)
        self.glob_filter_treeview.set_headers_visible(False)
        self.glob_filter_treeview_sel = self.glob_filter_treeview.get_selection()
        self.glob_filter_treeview_sel.set_mode(gtk.SELECTION_SINGLE)

        self.regex_filter_liststore = gtk.ListStore(str, str)
        self.regex_filter_treeview.set_model(self.regex_filter_liststore)
        add_text_column(self.regex_filter_treeview, 'Name', 0)
        add_text_column(self.regex_filter_treeview, 'Regular Expression', 1)
        self.regex_filter_treeview.set_headers_visible(False)
        self.regex_filter_treeview_sel = self.regex_filter_treeview.get_selection()
        self.regex_filter_treeview_sel.set_mode(gtk.SELECTION_SINGLE)

        def entry_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Return':
                self.save()
                return True
            return False
        self.name_entry.connect("key-press-event", entry_keypress)
        self.dir_entry.connect("key-press-event", entry_keypress)

        def browse_clicked(widget):
            dialog = gtk.FileChooserDialog("Choose Directory",
                                       self.editor.window,
                                       gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            #dialog.set_show_hidden(False)
            dialog.set_default_response(gtk.RESPONSE_OK)

            current_path = self.dir_entry.get_text()
            if os.path.exists(current_path):
                dialog.set_current_folder(current_path)
            else:
                dialog.set_current_folder(os.path.expanduser('~'))

            response = dialog.run()
            dialog.hide()

            if response == gtk.RESPONSE_OK:
                path = dialog.get_filename()
                path = path.decode(sys.getfilesystemencoding())
                path = path.encode('utf8')
                self.dir_entry.set_text(path)
            try:
                dialog.destroy()
            except AttributeError:
                pass
        self.browse_button.connect("clicked", browse_clicked)

        def window_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Escape':
                self.window.hide()
            return False
        self.window.connect("key-press-event", window_keypress)

        def window_delete_event(widget, event):
            self.window.hide()
            return True
        self.window.connect("delete_event", window_delete_event)

        def add_exclude(entry, liststore):
            liststore.append([entry.get_text()])
            entry.set_text('')

        def add_exclude_keypress(widget, event, liststore):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Return':
                add_exclude(widget, liststore)
                return True
            return False
        self.glob_exclude_entry.connect("key-press-event",
                                        add_exclude_keypress,
                                        self.glob_exclude_liststore)
        self.regex_exclude_entry.connect("key-press-event",
                                         add_exclude_keypress,
                                         self.regex_exclude_liststore)

        def add_exclude_clicked(widget, entry, liststore):
            add_exclude(entry, liststore)
        self.glob_exclude_add_button.connect("clicked",
                                             add_exclude_clicked,
                                             self.glob_exclude_entry,
                                             self.glob_exclude_liststore)
        self.regex_exclude_add_button.connect("clicked",
                                              add_exclude_clicked,
                                              self.glob_exclude_entry,
                                              self.regex_exclude_liststore)

        def add_filter(name_entry, pattern_entry, liststore):
            name = name_entry.get_text()
            pattern = pattern_entry.get_text()
            # TODO: validate pattern
            if name and pattern:
                liststore.append([name, pattern])
                name_entry.set_text('')
                pattern_entry.set_text('')
            else:
                # TODO: some kind of feedback that states you need to fill in both
                pass

        def add_filter_keypress(widget, event, name_entry, pattern_entry,
                                liststore):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Return':
                add_filter(name_entry, pattern_entry, liststore)
                return True
            return False
        self.glob_filter_name_entry.connect("key-press-event",
                                            add_filter_keypress,
                                            self.glob_filter_name_entry,
                                            self.glob_filter_pattern_entry,
                                            self.glob_filter_liststore)
        self.glob_filter_pattern_entry.connect("key-press-event",
                                               add_filter_keypress,
                                               self.glob_filter_name_entry,
                                               self.glob_filter_pattern_entry,
                                               self.glob_filter_liststore)
        self.regex_filter_name_entry.connect("key-press-event",
                                             add_filter_keypress,
                                             self.regex_filter_name_entry,
                                             self.regex_filter_pattern_entry,
                                             self.regex_filter_liststore)
        self.regex_filter_pattern_entry.connect("key-press-event",
                                                add_filter_keypress,
                                                self.regex_filter_name_entry,
                                                self.regex_filter_pattern_entry,
                                                self.regex_filter_liststore)

        def add_filter_clicked(widget, name_entry, pattern_entry, liststore):
            add_filter(name_entry, pattern_entry, liststore)
        self.glob_filter_add_button.connect("clicked",
                                            add_filter_clicked,
                                            self.glob_filter_name_entry,
                                            self.glob_filter_pattern_entry,
                                            self.glob_filter_liststore)
        self.regex_filter_add_button.connect("clicked",
                                             add_filter_clicked,
                                             self.regex_filter_name_entry,
                                             self.regex_filter_pattern_entry,
                                             self.regex_filter_liststore)

        def exclude_row_activated(treeview, path, view_column):
            self.edit_exclude_dialog.show(treeview, path, view_column)
        self.glob_exclude_treeview.connect('row-activated',
                                           exclude_row_activated)
        self.regex_exclude_treeview.connect('row-activated',
                                            exclude_row_activated)

        def filter_row_activated(treeview, path, view_column):
            self.edit_filter_dialog.show(treeview, path, view_column)
        self.glob_filter_treeview.connect('row-activated',
                                          filter_row_activated)
        self.regex_filter_treeview.connect('row-activated',
                                           filter_row_activated)


        def cancel_clicked(widget):
            self.window.hide()
        self.cancel_button.connect("clicked", cancel_clicked)

    def validate(self, workspace=None):
        errors = []

        # can we just assume this is ascii/utf8?
        name = self.name_entry.get_text().decode('utf8')
        dirpath = self.dir_entry.get_text().decode('utf8')
        slug = slugify(name)

        if not name:
            errors.append("Name is required.")
        elif workspace and slug != workspace.slug:
            if any((w.slug == slug for w in self.editor.workspaces)):
                errors.append("Name must be unique.")

        if not dirpath:
            errors.append("Root Directory is required.")
        elif not (os.path.exists(dirpath) and os.path.isdir(dirpath)):
            errors.append("Root Directory is not a valid directory.")

        m = self.glob_exclude_liststore
        i = m.get_iter_first()
        while i:
            next = m.iter_next(i)
            pattern = m.get_value(i, 0)
            if not pattern:
                m.remove(i) # just delete empty ones
            i = next

        m = self.regex_exclude_liststore
        i = m.get_iter_first()
        while i:
            next = m.iter_next(i)
            pattern = m.get_value(i, 0)
            if not pattern:
                m.remove(i) # just delete empty ones
            try:
                re.compile(pattern)
            except:
                err = "'%s' is not a valid regular expression." % (pattern,)
                errors.append(err)
            i = next

        filter_names = {}

        m = self.glob_filter_liststore
        i = m.get_iter_first()
        while i:
            next = m.iter_next(i)
            name = m.get_value(i, 0)
            pattern = m.get_value(i, 1)
            if not (name and pattern):
                m.remove(i) # just delete empty ones
            filter_names[name] = filter_names.get(name, 0) + 1
            i = next

        m = self.regex_filter_liststore
        i = m.get_iter_first()
        while i:
            next = m.iter_next(i)
            name = m.get_value(i, 0)
            pattern = m.get_value(i, 1)
            if not (name and pattern):
                m.remove(i) # just delete empty ones
            try:
                re.compile(pattern)
            except:
                err = "'%s' is not a valid regular expression." % (pattern,)
                errors.append(err)
            filter_names[name] = filter_names.get(name, 0) + 1
            i = next

        for name, count in filter_names.iteritems():
            if count > 1:
                err = "'%s' is used as a filter name multiple times." % (name,)
                errors.append(err)

        if errors:
            dialog = gtk.MessageDialog(self.editor.window,
                       gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                       gtk.MESSAGE_ERROR,
                       gtk.BUTTONS_OK,
                       "\n".join(errors))
            response = dialog.run()
            try:
                dialog.destroy()
            except AttributeError:
                pass

            return False

        else:
            return True

    def set_workspace_excludes_filters(self, workspace):
        exclude_globs = []
        m = self.glob_exclude_liststore
        i = m.get_iter_first()
        while i:
            pattern = m.get_value(i, 0).decode('utf8')
            exclude_globs.append(pattern)
            i = m.iter_next(i)
        workspace.exclude_globs = exclude_globs

        exclude_regulars = []
        m = self.regex_exclude_liststore
        i = m.get_iter_first()
        while i:
            pattern = m.get_value(i, 0).decode('utf8')
            exclude_regulars.append(pattern)
            i = m.iter_next(i)
        workspace.exclude_regulars = exclude_regulars

        filter_globs = {}
        m = self.glob_filter_liststore
        i = m.get_iter_first()
        while i:
            name = m.get_value(i, 0).decode('utf8')
            pattern = m.get_value(i, 1).decode('utf8')
            filter_globs[name] = pattern
            i = m.iter_next(i)
        workspace.filter_globs = filter_globs

        filter_regulars = {}
        m = self.regex_filter_liststore
        i = m.get_iter_first()
        while i:
            name = m.get_value(i, 0).decode('utf8')
            pattern = m.get_value(i, 1).decode('utf8')
            filter_regulars[name] = pattern
            i = m.iter_next(i)
        workspace.filter_regulars = filter_regulars

class GtkAddWorkspaceDialog(GtkWorkspaceDialog):
    def __init__(self, editor):
        super(GtkAddWorkspaceDialog, self).__init__(editor)

        # TODO: this should not be hardcoded here
        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'workspace_add.glade'))

        self.common_init(g)

        self.window.set_title('Add Workspace')
        self.add_button = g.get_widget('add_button')

        def add_clicked(widget):
            self.save()
        self.add_button.connect("clicked", add_clicked)

    def clear(self):
        self.name_entry.set_text('')
        self.dir_entry.set_text('')
        self.glob_exclude_liststore.clear()
        self.glob_exclude_entry.set_text('')
        self.regex_exclude_liststore.clear()
        self.regex_exclude_entry.set_text('')
        self.glob_filter_liststore.clear()
        self.glob_filter_name_entry.set_text('')
        self.glob_filter_pattern_entry.set_text('')
        self.regex_filter_liststore.clear()
        self.regex_filter_name_entry.set_text('')
        self.regex_filter_pattern_entry.set_text('')

    def save(self):
        if self.validate():
            name = self.name_entry.get_text().decode('utf8')
            root_path = self.dir_entry.get_text().decode('utf8')
            settings = self.editor.settings
            workspace = Workspace(settings, name, root_path)
            self.set_workspace_excludes_filters(workspace)
            workspace.save()

            self.editor.reload_workspaces()
            self.editor.switch_dialog.sync_workspace()
            self.editor.find_dialog.sync_workspace()

            self.window.hide()

            dialog = gtk.MessageDialog(self.editor.window,
               gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
               gtk.MESSAGE_QUESTION,
               gtk.BUTTONS_YES_NO,
               "Do you want to switch to the new workspace now?")

            response = dialog.run()
            try:
                dialog.destroy()
            except AttributeError:
                pass

            if response == gtk.RESPONSE_YES:
                self.editor.switch_workspace(workspace)

    def show(self):
        self.clear()
        self.notebook.set_current_page(0)
        self.window.show_all()

class GtkEditWorkspaceDialog(GtkWorkspaceDialog):
    def __init__(self, editor):
        super(GtkEditWorkspaceDialog, self).__init__(editor)

        # TODO: this should not be hardcoded here
        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'workspace_edit.glade'))

        self.common_init(g)

        self.save_button = g.get_widget('save_button')
        self.delete_button = g.get_widget('delete_button')

        def save_clicked(widget):
            self.save()
        self.save_button.connect("clicked", save_clicked)

        def delete_clicked(widget):
            dialog = gtk.MessageDialog(self.editor.window,
               gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
               gtk.MESSAGE_WARNING,
               gtk.BUTTONS_OK_CANCEL,
               "Are you sure you want to delete this workspace?")

            response = dialog.run()
            try:
                dialog.destroy()
            except AttributeError:
                pass

            if response == gtk.RESPONSE_OK:
                self.editor.workspace.delete()

                self.editor.switch_workspace(None)

                self.window.hide()

        self.delete_button.connect("clicked", delete_clicked)

    def save(self):
        workspace = self.editor.workspace
        if self.validate(workspace):
            name = self.name_entry.get_text().decode('utf8')
            root_path = self.dir_entry.get_text().decode('utf8')

            workspace.name = name
            workspace.root_path = root_path
            self.set_workspace_excludes_filters(workspace)
            workspace.save()

            self.editor.reload_workspaces()
            self.editor.switch_dialog.sync_workspace()
            self.editor.find_dialog.sync_workspace()

            self.window.hide()

    def sync_to_workspace(self):
        w = self.editor.workspace

        self.name_entry.set_text(w.name)
        self.dir_entry.set_text(w.root_path)

        self.glob_exclude_liststore.clear()
        for p in w.exclude_globs:
            self.glob_exclude_liststore.append([p])

        self.glob_exclude_entry.set_text('')

        self.regex_exclude_liststore.clear()
        for p in w.exclude_regulars:
            self.regex_exclude_liststore.append([p])

        self.regex_exclude_entry.set_text('')

        self.glob_filter_liststore.clear()
        for k, v in w.filter_globs.iteritems():
            self.glob_filter_liststore.append([k, v])

        self.glob_filter_name_entry.set_text('')
        self.glob_filter_pattern_entry.set_text('')

        self.regex_filter_liststore.clear()
        for k, v in w.filter_regulars.iteritems():
            self.regex_filter_liststore.append([k, v])

        self.regex_filter_name_entry.set_text('')
        self.regex_filter_pattern_entry.set_text('')

    def show(self):
        if self.editor.workspace:
            self.window.set_title('Edit workspace '+self.editor.workspace.name)
            self.sync_to_workspace()
            self.window.show_all()

class GtkEditExcludeDialog(object):
    def __init__(self, editor, parent):
        self.editor = editor

        # TODO: this should not be hardcoded here
        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'exclude_edit.glade'))

        self.window = g.get_widget('window')

        self.window.set_transient_for(parent)
        self.window.set_title('Edit exclude pattern')

        self.pattern_entry = g.get_widget('pattern_entry')
        self.delete_button = g.get_widget('delete_button')
        self.cancel_button = g.get_widget('cancel_button')
        self.save_button = g.get_widget('save_button')

        self.liststore = None
        self.path = None

        def window_delete_event(widget, event):
            self.window.hide()
            return True
        self.window.connect("delete_event", window_delete_event)

        def window_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Escape':
                self.window.hide()
                return True
            return False
        self.window.connect("key-press-event", window_keypress)

        def entry_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Return':
                self.save()
                return True
            return False
        self.pattern_entry.connect("key-press-event", entry_keypress)

        def save_clicked(widget):
            self.save()
        self.save_button.connect('clicked', save_clicked)

        def delete_clicked(widget):
            self.delete()
        self.delete_button.connect('clicked', delete_clicked)

        def cancel_clicked(widget):
            self.window.hide()
        self.cancel_button.connect('clicked', cancel_clicked)

    def save(self):
        i = self.liststore.get_iter(self.path)
        self.liststore.set_value(i, 0, self.pattern_entry.get_text())
        self.window.hide()

    def delete(self):
        i = self.liststore.get_iter(self.path)
        self.liststore.remove(i)
        self.window.hide()

    def show(self, treeview, path, view_column):
        self.liststore = treeview.get_model()
        self.path = path

        i = self.liststore.get_iter(path)
        pattern = self.liststore.get(i, 0)[0]

        self.pattern_entry.set_text(pattern)

        self.window.show()


class GtkEditFilterDialog(object):
    def __init__(self, editor, parent):
        self.editor = editor

        # TODO: this should not be hardcoded here
        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'filter_edit.glade'))

        self.window = g.get_widget('window')
        self.name_entry = g.get_widget('name_entry')
        self.pattern_entry = g.get_widget('pattern_entry')
        self.delete_button = g.get_widget('delete_button')
        self.cancel_button = g.get_widget('cancel_button')
        self.save_button = g.get_widget('save_button')

        self.window.set_transient_for(parent)
        self.window.set_title('Edit filter')

        self.liststore = None
        self.path = None

        def window_delete_event(widget, event):
            self.window.hide()
            return True
        self.window.connect("delete_event", window_delete_event)

        def window_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Escape':
                self.window.hide()
                return True
            return False
        self.window.connect("key-press-event", window_keypress)

        def entry_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Return':
                self.save()
                return True
            return False
        self.name_entry.connect("key-press-event", entry_keypress)
        self.pattern_entry.connect("key-press-event", entry_keypress)

        def save_clicked(widget):
            self.save()
        self.save_button.connect('clicked', save_clicked)

        def delete_clicked(widget):
            self.delete()
        self.delete_button.connect('clicked', delete_clicked)

        def cancel_clicked(widget):
            self.window.hide()
        self.cancel_button.connect('clicked', cancel_clicked)

    def save(self):
        i = self.liststore.get_iter(self.path)
        self.liststore.set_value(i, 0, self.name_entry.get_text())
        self.liststore.set_value(i, 1, self.pattern_entry.get_text())
        self.window.hide()

    def delete(self):
        i = self.liststore.get_iter(self.path)
        self.liststore.remove(i)
        self.window.hide()

    def show(self, treeview, path, view_column):
        self.liststore = treeview.get_model()
        self.path = path

        i = self.liststore.get_iter(path)
        name, pattern = self.liststore.get(i, 0, 1)

        self.name_entry.set_text(name)
        self.pattern_entry.set_text(pattern)

        self.window.show()
