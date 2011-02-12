import os
import gtk, pango
from ni.core.document import Document, load_document
from ni.editors.base.editor import Editor
from ni.editors.gtk.dialogs import *
from ni.editors.gtk.textarea import GTKTextarea
from ni.editors.gtk.view import GTKView
from ni.actions.base import *
from ni.actions.defaultactions import *
from ni.core.text import tab_len
from ni.core.dirtree import RootDirNode, FileNode
from ni.editors.gtk.menu import get_menu_xml, get_actions
from ni.editors.gtk.settings import load_gtk_settings
from ni.core.recent import get_recent_files, format_recent_line


# TODO: we have linesep_map variables all over the place... clean up.
linesep_map = {'\n': 1, '\r\n': 2, '\r': 3}

class GTKEditor(Editor):
    def __init__(self):
        super(GTKEditor, self).__init__()

        # settings
        self.settings = load_gtk_settings()

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.on_window_delete_event)
        self.window.connect("destroy", self.on_window_destroy)

        self.window.connect("configure_event", self.on_window_configure)

        width = self.settings.win_width
        height = self.settings.win_height
        self.window.set_default_size(width, height)

        x = self.settings.win_x
        y = self.settings.win_y
        self.window.move(x, y)

        self.vbox = gtk.VBox()
        self.window.add(self.vbox)

        # Actions and action groups:

        actions = get_actions(self)

        self.global_accelgroup = gtk.AccelGroup()
        self.window.add_accel_group(self.global_accelgroup)

        self.selection_accelgroup = gtk.AccelGroup()
        self.window.add_accel_group(self.selection_accelgroup)

        self.global_actiongroup = gtk.ActionGroup('global')
        self.selection_actiongroup = gtk.ActionGroup('selection')

        # global actions
        self.global_actiongroup.add_actions(actions['actions'])
        self.global_actiongroup.add_toggle_actions(actions['toggle_actions'])
        linesep_value = linesep_map[self.settings.linesep]

        edit_ws_action = self.global_actiongroup.get_action('EditWorkspace')
        edit_ws_action.set_sensitive(False)
        clear_wsc_action = self.global_actiongroup.get_action('ClearWorkspaceCache')
        clear_wsc_action.set_sensitive(False)

        for action in self.global_actiongroup.list_actions():
            action.set_accel_group(self.global_accelgroup)
            action.connect_accelerator()
            if action.get_name() == 'Undo':
                self.undo_action = action
            if action.get_name() == 'Redo':
                self.redo_action = action
        self.global_actiongroup.set_sensitive(True)
        self.global_actiongroup.set_visible(True)

        self.undo_action.set_sensitive(False)
        self.redo_action.set_sensitive(False)

        # things you can do with selections
        self.selection_actiongroup.add_actions(actions['selection_actions'])

        for action in self.selection_actiongroup.list_actions():
            action.set_accel_group(self.selection_accelgroup)
            action.connect_accelerator()
        self.selection_actiongroup.set_sensitive(False)
        self.selection_actiongroup.set_visible(True)

        # uimanager, menu
        uimanager = gtk.UIManager()
        uimanager.insert_action_group(self.global_actiongroup, 0)
        uimanager.insert_action_group(self.selection_actiongroup, -1)
        uimanager.add_ui_from_string(get_menu_xml())
        uimanager.ensure_update() # is this really necessary?
        toplevels = uimanager.get_toplevels(gtk.UI_MANAGER_MENUBAR)
        self.menubar = toplevels[0]
        self.vbox.pack_start(self.menubar, expand=False)
        self.uimanager = uimanager

        # workspaces
        self.workspace_merge_id = None
        self.workspaces_actiongroup = gtk.ActionGroup('workspaces')
        self.uimanager.insert_action_group(self.workspaces_actiongroup, -1)
        #self._sync_workspaces_menu()
        self.reload_workspaces()

        # colourschemes
        self.colourschemes = self.settings.load_colourschemes()
        # sane default that will be overridden in a moment:
        self.colourscheme = self.colourschemes[0]
        self.set_colourscheme(self.settings.colourscheme)

        uimanager.ensure_update()

        # statusbar
        self.status_hbox = gtk.HBox(spacing=0)
        self.vbox.pack_end(self.status_hbox, expand=False)

        self.status_message = gtk.Label()
        self.status_modified = gtk.Label()
        self.status_position = gtk.Label()
        self.status_lexer = gtk.Label()
        self.status_linesep = gtk.Label()
        self.status_encoding = gtk.Label()

        self.status_message.set_alignment(0, 0)
        self.status_modified.set_alignment(0, 0)
        self.status_position.set_alignment(0, 0)
        self.status_lexer.set_alignment(1, 0)

        self.status_position.set_size_request(100, -1)
        self.status_lexer.set_size_request(150, -1)

        self.status_message.set_padding(3, 3)
        self.status_modified.set_padding(3, 3)
        self.status_position.set_padding(3, 3)
        self.status_lexer.set_padding(3, 3)
        self.status_linesep.set_padding(3, 3)
        self.status_encoding.set_padding(3, 3)

        self.status_hbox.pack_start(self.status_message, expand=True)
        self.status_hbox.pack_start(self.status_modified, expand=False)
        self.status_hbox.pack_start(self.status_position, expand=False)
        self.status_hbox.pack_start(self.status_lexer, expand=False)
        self.status_hbox.pack_start(self.status_linesep, expand=False)
        self.status_hbox.pack_start(self.status_encoding, expand=False)

        self.vpaned = gtk.VPaned()

        self.hpaned = gtk.HPaned()

        self.vbox.pack_end(self.hpaned, expand=True)

        self.document_tree_model = gtk.TreeStore(str, str, bool)

        self.document_tree = gtk.TreeView(self.document_tree_model)
        self.document_tree.unset_flags(gtk.CAN_FOCUS)
        column_filename = gtk.TreeViewColumn('Documents')
        self.document_tree.append_column(column_filename)

        cell_filename = gtk.CellRendererText()
        column_filename.pack_end(cell_filename)
        column_filename.add_attribute(cell_filename, 'text', 0)
        def cb(column, cell_renderer, tree_model, iterrow):
            doc = self.textarea.view.document
            filepath = tree_model.get_value(iterrow, 1)
            if filepath in (doc.location, doc.description):
                cell_renderer.set_property('weight', pango.WEIGHT_BOLD)
            else:
                cell_renderer.set_property('weight', pango.WEIGHT_NORMAL)
        column_filename.set_cell_data_func(cell_filename, cb)

        self.column_filename = column_filename

        self.scrolled_window = gtk.ScrolledWindow()

        self.scrolled_window.add(self.document_tree)
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)
        self.hpaned.pack1(self.scrolled_window, resize=False, shrink=False)

        # textarea
        self.textarea = GTKTextarea(self)

        # replace with something to load the session
        recent_files_path = self.settings.get_recent_files_path()
        if os.path.exists(recent_files_path):
            for r in get_recent_files(recent_files_path):
                path, scroll_pos, cursor_pos = r
                if os.path.exists(path) and os.path.isfile(path):
                    view = self.new_view(path)
                    view.cursor_pos = cursor_pos
                    view.scroll_pos = scroll_pos
                    view.last_x_pos = cursor_pos[1]
                    self.switch_current_view(view) # to trigger scroll

        # if the most recent file is set in settings, try and switch to it.
        # (it will have to be set in the recent files list to be loaded)
        if self.settings.most_recent_file:
            for view in self.views:
                if view.document.location == self.settings.most_recent_file:
                    self.switch_current_view(view)
                    break

        if not self.views:
            self.new_view()

        def add(widget):
            #self.hpaned.pack2(widget, resize=True, shrink=False)
            self.vpaned.pack1(widget, resize=False, shrink=True)
        self.textarea.attach(add)

        self.search_notebook = gtk.Notebook()
        self.search_notebook.set_property('tab-vborder', 0)
        self.vpaned.pack2(self.search_notebook, resize=True, shrink=True)

        self.search_notebook.connect("switch-page",
                                     self.on_search_notebook_switch_page)

        self.hpaned.pack2(self.vpaned, resize=True, shrink=False)

        self.window.show_all()
        self.textarea.show() # hack because some stuff can't be initialised
                            # earlier

        self.search_notebook.hide()

        self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)

        self.scrolled_window_visible = True

        self.document_tree.set_size_request(200, -1) # ??
        self.document_tree.connect("cursor-changed",
                                    self.on_document_tree_cursor_changed)
        self.document_tree.expand_all()

        self._select_current_view_in_tree()

        if not self.settings.show_statusbar:
            self.status_hbox.hide()

        if not self.settings.show_sidebar:
            self.scrolled_window_visible = False
            self.scrolled_window.hide()

        self.open_dialog = GtkOpenDialog(self)
        self.save_dialog = GtkSaveDialog(self)
        self.goto_dialog = GtkGotoLineDialog(self)
        self.switch_dialog = GtkSwitchDocumentDialog(self)
        self.add_workspace_dialog = GtkAddWorkspaceDialog(self)
        self.edit_workspace_dialog = GtkEditWorkspaceDialog(self)
        self.preferences_dialog = GtkPreferencesDialog(self)
        self.find_dialog = GtkFindDialog(self)

        # pre-select the workspace
        for w in self.workspaces:
            if w.name == self.settings.workspace:
                self.switch_workspace(w)
                break

    ### Editor overrides

    def exit(self):
        """Cause the editor to exit asap."""
        self.save_settings()

        for search in self.searches:
            self.cancel_search(search)

        unsaved = 0
        for view in self.views:
            if view.document.is_modified:
                unsaved += 1
        if unsaved:
            dialog = GtkConfirmExitDialog(self)
            if dialog.show():
                gtk.main_quit()
        else:
            gtk.main_quit()

    def _sync_workspaces_menu(self):
        # remove the menu
        if self.workspace_merge_id:
            self.uimanager.remove_ui(self.workspace_merge_id)

        # clear the actions
        for action in self.workspaces_actiongroup.list_actions():
            self.workspaces_actiongroup.remove_action(action)

        # workspace actions
        workspace_actions = []
        action = ("SelectNoWorkspace", None, "None", None, None, 0)
        workspace_actions.append(action)
        index = 0
        value = 0
        for w in self.workspaces:
            index += 1
            slug = "SelectWorkspace_"+w.slug
            action = (slug, None, w.name, None, None, index)
            workspace_actions.append(action)
            if self.workspace and w.slug == self.workspace.slug:
                value = index
        self.workspaces_actiongroup.add_radio_actions(
            workspace_actions,
            value=value,
            on_change=self.change_workspace_callback,
            user_data=None)
        self.workspaces_actiongroup.set_sensitive(True)
        self.workspaces_actiongroup.set_visible(True)

        # workspace menu items
        merge_id = self.uimanager.new_merge_id()
        self.workspace_merge_id = merge_id
        self.uimanager.add_ui(merge_id,
                              'ui/menubar/WorkspacesMenu',
                              "None",
                              "SelectNoWorkspace",
                              gtk.UI_MANAGER_MENUITEM,
                              False)
        for w in self.workspaces:
            self.uimanager.add_ui(merge_id,
                                  'ui/menubar/WorkspacesMenu',
                                  w.name,
                                  "SelectWorkspace_"+w.slug,
                                  gtk.UI_MANAGER_MENUITEM,
                                  False)

    def reload_workspaces(self):
        self.workspaces = self.settings.load_workspaces()
        self._sync_workspaces_menu()

    def switch_workspace(self, workspace):
        # this is for when we change the workspace from code elsewhere

        self.workspace = workspace
        sensitive = bool(workspace)
        edit_ws_action = self.global_actiongroup.get_action('EditWorkspace')
        edit_ws_action.set_sensitive(sensitive)
        clear_wsc_action = self.global_actiongroup.get_action('ClearWorkspaceCache')
        clear_wsc_action.set_sensitive(sensitive)

        # TODO: this (like many other bits of code) should probably use some
        # signal/callback/multi-dispatch system.
        self.switch_dialog.sync_workspace()
        self.find_dialog.sync_workspace()

        self.reload_workspaces()

        self.update_status()

    def change_workspace_callback(self, from_action, to_action):
        # this is the callback when the user picks a workspace from the menu

        edit_ws_action = self.global_actiongroup.get_action('EditWorkspace')
        clear_wsc_action = self.global_actiongroup.get_action('ClearWorkspaceCache')

        name = to_action.get_name()
        bits = name.split('_')
        if len(bits) > 1:
            slug = bits[1]
            for w in self.workspaces:
                if w.slug == slug:
                    self.workspace = w
                    edit_ws_action.set_sensitive(True)
                    clear_wsc_action.set_sensitive(True)
                    break

        else:
            self.workspace = None
            edit_ws_action.set_sensitive(False)
            clear_wsc_action.set_sensitive(False)

        # TODO: this (like many other bits of code) should probably use some
        # signal/callback/multi-dispatch system.
        self.switch_dialog.sync_workspace()
        self.find_dialog.sync_workspace()

        self.update_status()

    def _reset_document_tree_model(self, extra_expand=None):
        dtm = self.document_tree_model
        dt = self.document_tree

        # get all the paths to the files inside the expanded directories so
        # we can expand the tree again after we rebuild it
        expanded_dirs = []
        expanded_files = []
        def get_expanded(model, path, iterrow):
            if dt.row_expanded(path):
                expanded_dirs.append(dtm.get_value(iterrow, 1))
        dtm.foreach(get_expanded)
        if expanded_dirs:
            for v in self.views:
                location = v.document.location
                if location:
                    dirname = os.path.dirname(location) + os.path.sep
                    if dirname in expanded_dirs:
                        expanded_files.append(location)

        # now clear the tree
        dtm.clear()

        # add all the document locations into the tree
        root = RootDirNode()
        for v in self.views:
            if v.document.location:
                root.add(v.document.location)
            else:
                # add unsaved documents to the top
                row = (v.document.description, v.document.description, True)
                dtm.append(None, row)
        root.collapse()
        node_dict = {} # hmm.. should we keep this around?
        def add(node, parent_path):
            if parent_path:
                parent = node_dict[parent_path]
            else:
                parent = None
            name = node.path.replace(parent_path, '', 1)
            path = node.path
            is_file = isinstance(node, FileNode)
            node_dict[path] = dtm.append(parent, (name, path, is_file))
        if root.dirs or root.files:
            root.walk(add)

        if extra_expand:
            expanded_files.append(extra_expand)

        # expand up to all the files we had expanded before, put the cursor on
        # the selected file
        #doc = self.textarea.view.document
        def set_expanded(model, path, iterrow):
            filepath = dtm.get_value(iterrow, 1)

            if filepath in expanded_files:
                iterparent = dtm.iter_parent(iterrow)
                path = dtm.get_path(iterparent)
                dt.expand_to_path(path)
        dtm.foreach(set_expanded)

    def new_view(self, location=None):
        s = self.settings

        if location:
            for view in self.views:
                if view.document.location == location:
                    self.switch_current_view(view, False)
                    # We don't currently support multiple views on the same
                    # document, so exit out of the method
                    # TODO: should we reload?
                    return

            document = load_document(location, self.settings)
        else:
            title = self.get_next_title()
            document = Document(encoding=s.file_encoding,
                                linesep=s.linesep,
                                tab_size=s.tab_size,
                                title=title)
        view = GTKView(self, document)
        self.views.append(view)

        # Switch the view. switch_current_view will rebuild the tree to reflect
        # the selected view
        self.switch_current_view(view, True)

        #if view.document.is_modified:
        #    dialog = GtkWarnModifiedDialog(self)
        #    dialog.show()

        return view

    def copy_view(self):
        doc = self.textarea.view.document
        title = self.get_next_title()
        new_doc = Document(encoding=doc.encoding,
                           linesep=doc.linesep,
                           tab_size=doc.tab_size,
                           title=title)
        new_doc.insert(0, doc.content)
        new_view = GTKView(self, new_doc)
        self.views.append(new_view)
        self.switch_current_view(new_view, True)
        return new_view

    def close_view(self, view=None):
        if not view:
            view = self.textarea.view

        if view == self.previous_view:
            self.previous_view = None

        if view == self.textarea.view:
            if view.document.is_modified:
                dialog = GtkConfirmCloseDialog(self)
                if not dialog.show():
                    return

            if len(self.views) > 1:
                next = self.get_next_view()
                self.views.remove(view)
                # TODO: eh?
                #for search in self.searches:
                    #if self.view == view:
                    #    self.cancel_search(search)
                self.switch_current_view(next, True)
            else:
                self.views.remove(view)
                self.new_view()

    def switch_current_view(self, view, rebuild=False):
        """Switch the active document to the one specified."""

        if not view in self.views:
            raise Exception("Invalid document.")

        # set the previous view as this view
        try:
            if view != self.textarea.view:
                self.previous_view = self.textarea.view
        except AttributeError:
            pass # first time around

        # set the current view
        self.textarea.view = view
        
        # set the scrollbars' position to match the view's scroll_pos
        self.textarea.sync_scroll_pos()
        
        # set the scrollbars' ranges to match that of the view
        self.textarea.adjust_adjustments()

        # see textarea.draw()
        view.just_switched = True

        # set the window title
        #self.window.set_title(view.document.description)
        self.update_status()

        if rebuild:
            # rebuild the tree to reflect the change
            self._reset_document_tree_model(view.document.location)
        else:
            self.document_tree.queue_draw()

        # make sure things get redrawn
        self.textarea.redraw()

        self._select_current_view_in_tree()

    def _select_current_view_in_tree(self):
        def set_cursor(model, path, iterrow, (location, title)):
            l = self.document_tree_model.get_value(iterrow, 1)
            if l in (location, title):
                self.document_tree.get_selection().select_path(path)
                return True

        # make sure the current view is the selected one
        doc = self.textarea.view.document
        self.document_tree_model.foreach(set_cursor,
                                         (doc.location, doc.description))

    def get_next_view(self):
        # man this is horrible code...
        class FindNext(object):
            def __init__(self, editor):
                self.editor = editor
                self.dtm = editor.document_tree_model
                self.views = editor.views
                self.first = None
                self.found_current = False
                self.doc = editor.textarea.view.document
                self.next = None

            def callback(self, model, path, iterrow):
                location = self.dtm.get_value(iterrow, 1)
                if not self.first:
                    for view in self.views:
                        titles = (view.document.location,
                                  view.document.description)
                        if location in titles:
                            self.first = view
                            break
                if location in (self.doc.location, self.doc.description):
                    self.found_current = True
                else:
                    if self.found_current:
                        for view in self.views:
                            if not self.next:
                                titles = (view.document.location,
                                          view.document.description)
                                if location in titles:
                                    self.next = view

        dtm = self.document_tree_model
        fn = FindNext(self)
        dtm.foreach(fn.callback)
        if not fn.next and fn.first:
            fn.next = fn.first

        return fn.next

    def get_ordered_views(self):
        dtm = self.document_tree_model
        views = []

        def callback(model, path, iterrow):
            location = dtm.get_value(iterrow, 1)
            for view in self.views:
                titles = (view.document.location, view.document.description)
                if location in titles:
                    views.append(view)
                    break

        dtm.foreach(callback)
        return views

    def switch_to_next_view(self):
        next = self.get_next_view()
        if next:
            self.switch_current_view(next)

    def get_previous_view(self):
        # more horrible code...
        class FindPrevious(object):
            def __init__(self, editor):
                self.editor = editor
                self.dtm = editor.document_tree_model
                self.views = editor.views
                self.last = None
                self.doc = editor.textarea.view.document
                self.previous = None

            def callback(self, model, path, iterrow):
                location = self.dtm.get_value(iterrow, 1)

                if location in (self.doc.location, self.doc.description):
                    for view in self.views:
                        if not self.previous and self.last:
                            self.previous = self.last

                for view in self.views:
                    titles = (view.document.location,
                              view.document.description)
                    if location in titles:
                        self.last = view
                        break

        dtm = self.document_tree_model
        fn = FindPrevious(self)
        dtm.foreach(fn.callback)
        if not fn.previous and fn.last:
            fn.previous = fn.last
        return fn.previous

    def switch_to_previous_view(self):
        previous = self.get_previous_view()
        if previous:
            self.switch_current_view(previous)

    def copy_to_clipboard(self, view):
        if not view.selection:
            return

        text = view.selection.get_content()
        self.clipboard.set_text(text)

    def paste_from_clipboard(self, view):
        def paste_callback(clipboard, text, data):
            if not text or text == '':
                return

            action = InsertText(view, text)
            view.execute_action(action)

        self.clipboard.request_text(paste_callback)

    def toggle_sidebar(self):
        self.settings['show_sidebar'] = not self.settings.show_sidebar
        if self.scrolled_window_visible:
            self.scrolled_window_visible = False
            self.scrolled_window.hide()
        else:
            self.scrolled_window_visible = True
            self.scrolled_window.show()

    def toggle_gutter(self):
        self.settings['show_gutter'] = not self.settings.show_gutter
        self._redraw_view(self.textarea.view)

    def toggle_statusbar(self):
        show_statusbar = self.settings.show_statusbar
        if show_statusbar:
            self.status_hbox.hide()
        else:
            self.status_hbox.show()
        self.settings['show_statusbar'] = not show_statusbar

    def toggle_margin(self):
        self.settings['show_margin'] = not self.settings.show_margin
        self._redraw_view(self.textarea.view)

    def undo(self, view):
        super(GTKEditor, self).undo(view)
        self.update_undoredo()

    def redo(self, view):
        super(GTKEditor, self).redo(view)
        self.update_undoredo()

    def _get_view(self):
        return self.textarea.view

    def _redraw_view(self, view):
        self.textarea.redraw()

    def set_colourscheme(self, name):
        """Set self.colourscheme, change colours on all views."""

        for c in self.colourschemes:
            if c.name == name:
                self.colourscheme = c
                for v in self.views:
                    v.set_colours()
                break
        else:
            raise AssertionError("Colourscheme %s not found" % (name,))

    ### Other

    def save_settings(self):
        #print "save settings"
        x, y = self.window.get_position()

        self.settings['win_x'] = x
        self.settings['win_y'] = y
        location = self.textarea.view.document.location
        if location:
            self.settings['most_recent_file'] = location
        else:
            self.settings['most_recent_file'] = None

        if self.workspace:
            self.settings['workspace'] = self.workspace.name
        else:
            self.settings['workspace'] = None

        self.settings.save()

        # write the open list of files to a file so that we can load them up
        # next time the editor starts
        recent_files_path = self.settings.get_recent_files_path()
        fle = open(recent_files_path, "w")
        try:
            for view in self.views:
                location = view.document.location
                if location:
                    scroll_pos = view.scroll_pos
                    cursor_pos = view.cursor_pos 
                    line = format_recent_line(location, scroll_pos, cursor_pos)
                    line = line.encode('utf8')
                    fle.write(line+'\n')

        finally:
            fle.close()



    def action_callback(self, gtkaction):
        """This glues the gtk.Action things to ni Action classes."""

        action_name = gtkaction.get_name()
        if globals().has_key(action_name):
            cls = globals()[action_name]
            if issubclass(cls, Action):
                view = self.textarea.view
                action = cls(view)
                view.execute_action(action)
            else:
                print action_name, "is not a valid action."
        else:
            print action_name, "action does not exist."

        return True # not too sure if this should even return anything..

    def update_status(self):
        view = self.textarea.view
        doc = view.document

        if doc.tokenizer.lexer:
            mode = doc.tokenizer.lexer.name
        else:
            mode = "plain"

        y, x = view.cursor_pos

        line = doc.get_line(y)
        x = tab_len(line[:x], doc.tab_size)
        x += 1
        y += 1

        if doc.is_modified:
            modified = '*MODIFIED* '
            title = view.document.description+' (modified)'
        else:
            modified = ''
            title = view.document.description

        #if self.workspace and view.document.location:
        #    root_path = self.workspace.root_path
        #    if view.document.location[:len(root_path)] == root_path:
        #        title = "[workspace: %s] %s" % (self.workspace.name, title)

        # for now always put the workspace name in the titlebar (even if the
        # current file isn't part of the workspace)
        #if self.workspace:
        #    title = "%s | %s" % (title, self.workspace.name)

        self.window.set_title(title)

        # TODO: we have linesep_map variables all over the place... clean up.
        linesep_map = {'\n': 'UNIX', '\r\n': 'DOS/Windows', '\r': 'MacOS'}
        sep_type = linesep_map[doc.linesep or self.settings.linesep]

        self.status_modified.set_text(modified)
        self.status_position.set_text("Ln %s, Col %s" % (y, x))
        self.status_lexer.set_label(mode)
        self.status_linesep.set_text(sep_type)
        self.status_encoding.set_text(doc.encoding.upper())

    def update_undoredo(self):
        view = self.textarea.view
        doc = view.document

        if doc.undo_stack:
            self.undo_action.set_sensitive(True)
        else:
            self.undo_action.set_sensitive(False)
        if doc.redo_stack:
            self.redo_action.set_sensitive(True)
        else:
            self.redo_action.set_sensitive(False)

    ### Document Tree callbacks

    def on_search_notebook_switch_page(self, notebook, page, page_num):
        sw = notebook.get_nth_page(page_num)
        for search in self.searches:
            if search.scrolled_window == sw:
                self.search = search
                self.search.bulk_update()
                break

    def on_document_tree_cursor_changed(self, treeview):
        path, focus_column = treeview.get_cursor()
        if path:
            dtm = self.document_tree_model
            iterrow = dtm.get_iter(path)
            filepath = dtm.get_value(iterrow, 1)

            for view in self.views:
                titles = (view.document.location, view.document.description)
                if filepath in titles:
                    if view != self.textarea.view:
                        self.switch_current_view(view)
                    break


    ### Window callbacks

    def on_window_delete_event(self, widget, event, data=None):
        self.save_settings()

        for search in self.searches:
            self.cancel_search(search)

        unsaved = 0
        for view in self.views:
            if view.document.is_modified:
                unsaved += 1

        if unsaved:
            dialog = GtkConfirmExitDialog(self)
            return not dialog.show()
        else:
            return False

    def on_window_destroy(self, widget):
        gtk.main_quit()

    def on_window_configure(self, widget, event):
        self.settings['win_width'] = event.width
        self.settings['win_height'] = event.height


#if __name__ == "__main__":
#    editor = GTKEditor()
#    gtk.main()

