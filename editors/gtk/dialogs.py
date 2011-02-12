import os
import sys
import re
import gtk
import gtk.glade
import gobject
from threading import Thread
from ni.core.files import glob_match
from ni.editors.gtk.workspace_dialogs import GtkAddWorkspaceDialog
from ni.editors.gtk.workspace_dialogs import GtkEditWorkspaceDialog
from ni.editors.gtk.search import GtkSearch
from ni.editors.gtk.settings import GLADE_DIR
from ni.editors.base.search import SEARCH_SELECTION, SEARCH_DOCUMENT, \
                                   SEARCH_DOCUMENTS, \
                                   SEARCH_WORKSPACE, SEARCH_DIRECTORY


__all__ = ["GtkConfirmOverwriteDialog", "GtkConfirmCloseDialog",
    "GtkConfirmExitDialog", "GtkWarnModifiedDialog", "GtkOpenDialog",
    "GtkSaveDialog", "GtkGotoLineDialog", "GtkSwitchDocumentDialog",
    "GtkAddWorkspaceDialog", "GtkEditWorkspaceDialog", "GtkPreferencesDialog",
    "GtkFindDialog"]

class GtkConfirmOverwriteDialog(object):
    def __init__(self, editor, message=None):
        self.editor = editor
        if not message:
            message = "A file by that name exists. " + \
                      "Do you want to overwrite the file?"
        self.message = message

    def show(self):
        view = self.editor.textarea.view
        doc = view.document
        flags = gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT
        dialog = gtk.MessageDialog(self.editor.window,
                                   flags,
                                   gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK_CANCEL,
                                   self.message)

        response = dialog.run()
        try:
            dialog.destroy()
        except AttributeError:
            pass

        if response == gtk.RESPONSE_OK:
            return True
        else:
            return False

class GtkConfirmCloseDialog(object):
    def __init__(self, editor, message=None):
        self.editor = editor
        if not message:
            message = "You have unsaved changes. " + \
                      "Are you sure you want to close this file?"
        self.message = message

    def show(self):
        view = self.editor.textarea.view
        doc = view.document
        flags = gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT
        dialog = gtk.MessageDialog(self.editor.window,
                                   flags,
                                   gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK_CANCEL,
                                   self.message)

        response = dialog.run()
        try:
            dialog.destroy()
        except AttributeError:
            pass

        if response == gtk.RESPONSE_OK:
            return True
        else:
            return False

class GtkConfirmExitDialog(object):
    def __init__(self, editor, message=None):
        self.editor = editor
        if not message:
            message = "You have unsaved changes. " + \
                      "Are you sure you want to exit?"
        self.message = message

    def show(self):
        view = self.editor.textarea.view
        doc = view.document
        flags = gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT
        dialog = gtk.MessageDialog(self.editor.window,
                                   flags,
                                   gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK_CANCEL,
                                   self.message)

        response = dialog.run()
        try:
            dialog.destroy()
        except AttributeError:
            pass

        if response == gtk.RESPONSE_OK:
            return True
        else:
            return False

class GtkWarnModifiedDialog(object):
    def __init__(self, editor, message=None):
        self.editor = editor
        if not message:
            message = "The file contained tab characters which are not " +\
                      "currently supported, so they got automatically " +\
                      "replaced with spaces according to your indent " +\
                      "settings. If this is not what you want, then please " +\
                      "close the file without saving."
        self.message = message

    def show(self):
        view = self.editor.textarea.view
        doc = view.document
        flags = gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT
        dialog = gtk.MessageDialog(self.editor.window,
                                   flags,
                                   gtk.MESSAGE_WARNING,
                                   gtk.BUTTONS_OK,
                                   self.message)

        response = dialog.run()
        try:
            dialog.destroy()
        except AttributeError:
            pass

class GtkOpenDialog(object):
    def __init__(self, editor, message=None):
        self.editor = editor

    def show(self):
        view = self.editor.textarea.view
        doc = view.document
        buttons = (gtk.STOCK_CANCEL,
                   gtk.RESPONSE_CANCEL,
                   gtk.STOCK_OPEN,
                   gtk.RESPONSE_OK)
        dialog = gtk.FileChooserDialog("Open..",
                                       self.editor.window,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       buttons)
        dialog.set_select_multiple(True)
        #dialog.set_show_hidden(False)
        dialog.set_default_response(gtk.RESPONSE_OK)

        if doc.location:
            dialog.set_current_folder(os.path.dirname(doc.location))

        filtr = gtk.FileFilter()
        filtr.set_name("All files")
        filtr.add_pattern("*")
        dialog.add_filter(filtr)

        response = dialog.run()
        dialog.hide()

        if response == gtk.RESPONSE_OK:
            filenames = dialog.get_filenames()
            for filename in filenames:
                self.editor.new_view(filename)

        try:
            dialog.destroy()
        except AttributeError:
            pass


class GtkSaveDialog(object):
    def __init__(self, editor, message=None):
        self.editor = editor

    def show(self):
        view = self.editor.textarea.view
        doc = view.document

        dialog = gtk.FileChooserDialog("Save as..",
                                       self.editor.window,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        #dialog.set_show_hidden(False)
        dialog.set_default_response(gtk.RESPONSE_OK)

        if doc.location:
            dialog.set_current_folder(os.path.dirname(doc.location))

        filtr = gtk.FileFilter()
        filtr.set_name("All files")
        filtr.add_pattern("*")
        dialog.add_filter(filtr)

        response = dialog.run()
        dialog.hide()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            if os.path.exists(filename):
                dialog = GtkConfirmOverwriteDialog(self.editor)
                if dialog.show():
                    # make sure we don't have multiple copies of the file open
                    for view in self.editor.views:
                        if view.document.location == filename and view != view:
                            self.editor.views.remove(view)

                    doc.save(filename)
                    # this should update the tree, titlebar, etc.
                    self.editor.switch_current_view(view, True)
            else:
                doc.save(filename)
                # this should update the tree, titlebar, etc.
                self.editor.switch_current_view(view, True)

        try:
            dialog.destroy()
        except AttributeError:
            pass

class GtkGotoLineDialog(object):
    def __init__(self, editor):
        self.editor = editor

        # TODO: this should not be hardcoded here
        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'goto_line.glade'))
        self.window = g.get_widget('window')
        self.window.set_transient_for(self.editor.window)
        self.window.set_title('Go To Line')
        self.window.set_resizable(False)

        self.cancel_button = g.get_widget('cancel_button')
        self.jump_button = g.get_widget('jump_button')
        self.spinbutton = g.get_widget('spinbutton')

        def jump():
            self.spinbutton.update()
            line_num = int(self.spinbutton.get_value_as_int())
            
            view = self.editor.textarea.view
            offset = view.document.cursor_pos_to_offset((line_num-1, 0))
            view.cursor_pos = view.document.offset_to_cursor_pos(offset)
            #view.textarea.adjust_adjustments()
            view.check_cursor()
            
            self.window.hide()

        def jump_clicked(widget):
            jump()

        def cancel_clicked(widget):
            self.window.hide()

        self.jump_button.connect('clicked', jump_clicked)
        self.cancel_button.connect('clicked', cancel_clicked)

        def window_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Escape':
                self.window.hide()
                return True

            elif not self.cancel_button.is_focus() and keyname == "Return":
                jump()
                return True

            return False

        def window_delete_event(widget, event):
            self.window.hide()
            return True

        self.window.connect("key-press-event", window_keypress)
        self.window.connect("delete_event", window_delete_event)

    def show(self):
        self.window.show_all()
        self.spinbutton.select_region(0, -1)

def pattern_char_generator(pattern):
    is_wildcard = False
    for char in pattern:
        if char == '/':
            yield True, is_wildcard, '/'
        elif char == '*':
            is_wildcard = True
            continue
        else: 
            yield False, is_wildcard, char
        is_wildcard = False

def get_match(pattern, path, skip=0):
    # wildcards at start and end are implied
    pattern = pattern.strip('*')
    
    # special-case a slash at the start
    pattern = pattern.lstrip('/')
    
    # by replacing spaces with wildcards we can do awesomebar 
    # style multi-word matches
    pattern = pattern.replace(' ', '*')
    
    start_slash = path[0] == '/'
    path_parts = path.strip('/').split('/')
    patterngen = pattern_char_generator(pattern)    
    score = 0
    markup = u''
    num_chars = 0
    
    try:
        is_slash, is_wildcard, pattern_char = patterngen.next()
        is_wildcard = True # so we don't have to match from the start
        
        for part_index, part in enumerate(path_parts):
            # is_wildcard = True # so for each part we don't match from the start
            
            if part_index > 0 or start_slash:
                # add the slash character (unless this is the first part and
                # we didn't start with a slash)
                num_chars += 1
                if is_slash:
                    markup += u'<b>/</b>'
                else:
                    markup += u'/'
            
            if is_slash: #  and num_chars > skip
                # we're starting a part, so consume the slash and move on to
                # the next character                
                is_slash, is_wildcard, pattern_char = patterngen.next()            
            elif not is_wildcard:
                # we didn't match, because we expected a non-slash char, but
                # recurse starting here in case we get a full match later
                return get_match(pattern, path, num_chars)
            
            for part_char in part:
                num_chars += 1
                
                if num_chars <= skip:
                    score += 1
                    markup += part_char
                    continue
                
                if is_slash:
                    # we're skipping this entire path part, so just increase
                    # the score
                    score += 1
                    markup += part_char
                
                elif part_char == pattern_char:
                    # we matched a specific character
                    markup += u'<b>%s</b>' % (part_char,)
                    is_slash, is_wildcard, pattern_char = patterngen.next()                    
                
                elif is_wildcard:
                    # this char is valid, because we're using a wildcard
                    score += 1
                    markup += part_char
                
                else:
                    # the next character is not matching the next pattern
                    # character, so the path doesn't match, but 
                    # recurse starting here in case we get a fullmatch later
                    return get_match(pattern, path, num_chars)
        
        if is_slash:
            # if we still have slashes left after we ran out of parts, 
            # then this part didn't match
            return None
        
        # ish. ugly...
        try:
            is_slash, is_wildcard, pattern_char = patterngen.next()
        except StopIteration:
            # No more characters left, so that's fine.
            pass
        else:
            # We're at the end, but there are still pattern characters 
            # left that have to match.
            return None
                
    except StopIteration:
        # there are no more characters left in the pattern            
        # add markup (and score?) for characters after the last pattern char
        if len(path)-num_chars > 0:        
            markup += path[-(len(path)-num_chars):]
    
    return dict(path=path, score=score, markup=markup)

class FindDocumentsThread(Thread):
    def __init__(self, *args, **kwargs):
        super(FindDocumentsThread, self).__init__(*args, **kwargs)
        self.interrupted = False

    def start(self, pattern, paths, tree, liststore, selection, label,
              fix_path=None):

        self.interrupted = False
        self.pattern = pattern
        self.paths = paths
        self.tree = tree
        self.liststore = liststore
        self.selection = selection
        self.label = label

        if fix_path:
            self.fix_path = fix_path
        else:
            self.fix_path = lambda x: x

        super(FindDocumentsThread, self).start()

    def run(self):
        pattern = self.pattern
        paths = self.paths
        liststore = self.liststore
        fix_path = self.fix_path
        list_selection = self.selection
        label = self.label

        def compare_matches(a, b):
            scorea = a[0]
            scoreb = b[0]

            if scorea < scoreb:
                return -1
            elif scorea > scoreb:
                return 1
            else:
                return 0

        liststore.clear()
        label.set_text('Searching... <esc> to cancel')

        matches = []
        for n, path in enumerate(paths):
            if self.interrupted:
                break

            relative_path = fix_path(path)

            if pattern:
                match = get_match(self.pattern, relative_path)
                if match == None:
                    continue                
                score = match['score']
                markup = match['markup']
                matches.append([score, path, markup])

            else:
                matches.append([0, path, relative_path])

        #print "done"

        if self.interrupted:
            label.set_text('')
            liststore.clear()

        else:
            matches.sort(compare_matches)

            self.tree.set_model(None)
            for match in matches:
                liststore.append(match)
            self.tree.set_model(liststore)

            results = '%s results' % (len(matches),)
            label.set_text(results)

            list_selection.select_path(0)

class GtkSwitchDocumentDialog(object):
    def __init__(self, editor):
        self.editor = editor

        self.thread = None

        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'switch_document3.glade'))
        self.window = g.get_widget('window')
        self.window.set_transient_for(self.editor.window)
        self.window.set_title('Switch Document')

        # score, full path, display path
        self.liststore = gtk.ListStore(int, str, str)
        self.treeview = g.get_widget('treeview')
        self.treeview.set_model(self.liststore)
        column_path = gtk.TreeViewColumn('Filename')
        cell_path = gtk.CellRendererText()
        column_path.pack_start(cell_path)
        column_path.add_attribute(cell_path, 'markup', 2)
        self.treeview.append_column(column_path)
        self.treeview.set_headers_visible(False)
        self.liststore_sel = self.treeview.get_selection()
        self.liststore_sel.set_mode(gtk.SELECTION_MULTIPLE)

        self.filter_entry =  g.get_widget('filter_entry')
        self.cancel_button =  g.get_widget('cancel_button')
        self.open_button =  g.get_widget('open_button')
        self.results_label =  g.get_widget('results_label')
        self.radio_documents =  g.get_widget('radio_documents')
        self.radio_workspace =  g.get_widget('radio_workspace')

        self.workspace_filter = g.get_widget('workspace_filter')
        # type, pattern, name
        self.filter_liststore = gtk.ListStore(str, str, str)
        self.workspace_filter.set_model(self.filter_liststore)
        cell = gtk.CellRendererText()
        self.workspace_filter.clear()
        self.workspace_filter.pack_start(cell, True)
        self.workspace_filter.add_attribute(cell, 'text', 2)

        self.sync_workspace()

        def filter_entry_changed(widget, *args):
            self.do_find()

        def open_clicked(widget, *args):
            self.do_open()

        def close_clicked(widget, *args):
            self.stop()
            self.window.hide()

        def radio_toggled(widget, *args):
            self._paths = None
            self.do_find()
            self.filter_entry.grab_focus()

        def workspace_filter_changed(widget, *args):
            if self.radio_workspace.get_active():
                self.do_find()

        self.filter_entry.connect('changed', filter_entry_changed)
        self.cancel_button.connect('clicked', close_clicked)
        self.open_button.connect('clicked', open_clicked)
        self.radio_documents.connect('toggled', radio_toggled)
        self.radio_workspace.connect('toggled', radio_toggled)
        self.workspace_filter.connect('changed', workspace_filter_changed)
        self.treeview.connect('row-activated', open_clicked)

        def window_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Escape':
                self.stop()
                self.window.hide()

            elif self.filter_entry.is_focus():
                if keyname == "Return":
                    self.do_open()

                # really... there _must_ be an easier way. can't we just pass
                # the event along? or say "select the previous|next one"?
                elif keyname == "Down":
                    paths = self.liststore_sel.get_selected_rows()[1]

                    if paths:
                        last = paths[-1][0]
                        i = self.liststore.get_iter(last)
                        next = self.liststore.iter_next(i)
                        if next:
                            self.liststore_sel.unselect_all()
                            self.liststore_sel.select_iter(next)

                            # scroll
                            path = self.liststore.get_path(next)
                            self.treeview.scroll_to_cell(path)
                    else:
                        self.liststore_sel.unselect_all()
                        self.liststore_sel.select_path(0)

                    return True

                elif keyname == "Up":
                    paths = self.liststore_sel.get_selected_rows()[1]
                    self.liststore_sel.unselect_all()
                    if paths:
                        first = paths[0][0]
                        path = max(0, first-1)
                        self.liststore_sel.select_path(path)

                        # scroll
                        self.treeview.scroll_to_cell(path)
                    else:
                        self.liststore_sel.select_path(0)

                    return True

            return False

        def window_delete_event(widget, event):
            self.stop()
            self.window.hide()
            return True

        self.window.connect("key-press-event", window_keypress)
        self.window.connect("delete_event", window_delete_event)

        self._paths = None

    def get_paths(self):
        if self._paths == None:
            if self.radio_documents.get_active():
                # open documents
                views = self.editor.get_ordered_views()
                paths = [v.document.location for v in views \
                         if v.document.location]

            else:
                # files in workspace that match the selected filter
                i = self.workspace_filter.get_active_iter()
                p_type = self.filter_liststore.get_value(i, 0)
                p_name = self.filter_liststore.get_value(i, 1)
                
                if p_type == 'glob':                    
                    paths = self.editor.workspace.filepaths(glob_filter=p_name)
                else:
                    paths = self.editor.workspace.filepaths(re_filter=p_name)

            self._paths = list(paths)

        return self._paths

    def sync_workspace(self):
        self._paths = None

        self.filter_liststore.clear()
        # type, pattern, name
        self.filter_liststore.append(['glob', '*', 'All Files'])
        self.workspace_filter.set_active(0)

        workspace = self.editor.workspace

        if workspace:
            self.radio_workspace.props.sensitive = True
            self.workspace_filter.props.sensitive = True
        else:
            self.radio_workspace.set_active(False)
            self.radio_documents.set_active(True)
            self.radio_workspace.props.sensitive = False
            self.workspace_filter.props.sensitive = False

        if workspace:
            for name, pattern in workspace.filter_globs.iteritems():
                self.filter_liststore.append(['glob', pattern, name])
            for name, pattern in workspace.filter_regulars.iteritems():
                self.filter_liststore.append(['regex', pattern, name])

    def stop(self):
        if self.thread and self.thread.isAlive():
            self.thread.interrupted = True
            self.thread.join()

    def do_find(self):
        self.stop()

        pattern = self.filter_entry.get_text()

        paths = self.get_paths()

        self.thread = FindDocumentsThread()
        if self.radio_documents.get_active():
            self.thread.start(pattern, paths, self.treeview, self.liststore, \
                self.liststore_sel, self.results_label)
        else:
            fix_path = self.editor.workspace.fix_path
            self.thread.start(pattern, paths, self.treeview, self.liststore, \
                self.liststore_sel, self.results_label, fix_path)

    def do_open(self):
        paths = self.liststore_sel.get_selected_rows()[1]
        for path in paths:
            i = self.liststore.get_iter(path)
            location = self.liststore.get_value(i, 1)
            self.editor.new_view(location)
        self.stop()
        self.window.hide()

    def show(self):
        self.window.show_all()
        self.do_find()
        self.filter_entry.grab_focus()

def get_monospace_font_names(widget):
    context = widget.get_pango_context()
    monofonts = [fam for fam in context.list_families() if fam.is_monospace()]
    monofontnames = [f.get_name() for f in monofonts]
    monofontnames.sort()

    return monofontnames

def get_text_iter(liststore, text):
    i = liststore.get_iter_first()
    while (i):
        value = liststore.get(i, 0)[0]
        if value == text:
            return i
        i = liststore.iter_next(i)
    return None

encoding_map = {
    'utf8': 'UTF-8',
}

# TODO: we have linesep_map variables all over the place... clean up.
linesep_map = {
    '\n': 'Unix (\\n)',
    '\r\n': 'DOS/Windows (\\r\\n)',
    '\r': 'MacOS (\\r)',
}

class GtkPreferencesDialog(object):
    def __init__(self, editor):
        self.editor = editor

        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'global_settings3.glade'))
        self.window = g.get_widget('window')
        self.window.set_title('Preferences')
        self.window.set_transient_for(self.editor.window)

        self.notebook = g.get_widget('notebook')

        self.checkbutton_indent_spaces = g.get_widget('checkbutton_indent_spaces')
        self.spinbutton_tab_width = g.get_widget('spinbutton_tab_width')
        self.spinbutton_indent_width = g.get_widget('spinbutton_indent_width')
        self.spinbutton_right_margin = g.get_widget('spinbutton_right_margin')
        self.combobox_encoding = g.get_widget('combobox_encoding')
        self.combobox_separator = g.get_widget('combobox_separator')
        self.combobox_font = g.get_widget('combobox_font')
        self.close_button = g.get_widget('close_button')
        self.spinbutton_font_size = g.get_widget('spinbutton_font_size')
        self.treeview_colourscheme = g.get_widget('treeview_colourscheme')

        selection = self.treeview_colourscheme.get_selection()
        self.treeview_colourscheme_sel = selection

        # fill-in available options

        # encoding:
        enc_liststore = gtk.ListStore(str, str)
        self.combobox_encoding.set_model(enc_liststore)
        cell = gtk.CellRendererText()
        self.combobox_encoding.clear()
        self.combobox_encoding.pack_start(cell, True)
        self.combobox_encoding.add_attribute(cell, 'text', 1)
        for k, v in encoding_map.iteritems():
            enc_liststore.append([k, v])

        # separator:
        linesep_liststore = gtk.ListStore(str, str)
        self.combobox_separator.set_model(linesep_liststore)
        cell = gtk.CellRendererText()
        self.combobox_separator.clear()
        self.combobox_separator.pack_start(cell, True)
        self.combobox_separator.add_attribute(cell, 'text', 1)
        for k, v in linesep_map.iteritems():
            linesep_liststore.append([k, v])

        # fonts:
        font_liststore = gtk.ListStore(str)
        self.combobox_font.set_model(font_liststore)
        cell = gtk.CellRendererText()
        self.combobox_font.clear()
        self.combobox_font.pack_start(cell, True)
        self.combobox_font.add_attribute(cell, 'text', 0)
        self.combobox_font.add_attribute(cell, 'family', 0)

        monofontnames = get_monospace_font_names(self.window)
        for fontname in monofontnames:
            font_liststore.append([fontname])

        # colourschemes:
        colourscheme_liststore = gtk.ListStore(str)
        self.treeview_colourscheme.set_model(colourscheme_liststore)
        column_name = gtk.TreeViewColumn('Name')
        cell = gtk.CellRendererText()
        column_name.pack_start(cell, True)
        column_name.add_attribute(cell, 'text', 0)
        self.treeview_colourscheme.append_column(column_name)
        self.treeview_colourscheme.set_headers_visible(False)

        for c in self.editor.colourschemes:
            colourscheme_liststore.append([c.name])


        # callbacks

        def window_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Escape':
                self.window.hide()
                return True
            return False

        def window_delete_event(widget, event):
            self.window.hide()
            return True

        def close_clicked(widget):
            self.window.hide()

        self.window.connect("key-press-event", window_keypress)
        self.window.connect("delete_event", window_delete_event)
        self.close_button.connect("clicked", close_clicked)

        def change_cb(widget):
            if self.window.props.visible:
                settings = self.editor.settings

                # tab width:
                tab_size = int(self.spinbutton_tab_width.get_value())
                settings['tab_size'] = tab_size

                # indent width:
                indent_width = int(self.spinbutton_indent_width.get_value())
                settings['indent_width'] = indent_width

                # indent with spaces:
                indent_spaces = self.checkbutton_indent_spaces.get_active()
                settings['indent_spaces'] = indent_spaces

                # right margin:
                right_margin = int(self.spinbutton_right_margin.get_value())
                settings['right_margin'] = right_margin

                # line sep:
                i = self.combobox_separator.get_active_iter()
                linesep = self.combobox_separator.get_model().get_value(i, 0)
                settings['linesep'] = linesep

                # encoding:
                i = self.combobox_encoding.get_active_iter()
                encoding = self.combobox_encoding.get_model().get_value(i, 0)
                settings['file_encoding'] = encoding

                # font name, size:
                i = self.combobox_font.get_active_iter()
                fontname = self.combobox_font.get_model().get_value(i, 0)
                settings['font_name'] = fontname
                fontsize = int(self.spinbutton_font_size.get_value())
                settings['font_size'] = fontsize
                self.editor.textarea.set_font("%s %s" % (fontname, fontsize))

                # colourscheme:
                m, i = self.treeview_colourscheme_sel.get_selected()
                colourscheme = m.get_value(i, 0)
                settings['colourscheme'] = colourscheme
                self.editor.set_colourscheme(colourscheme)

                # force redraw:
                self.editor.textarea.draw()


        self.checkbutton_indent_spaces.connect("toggled", change_cb)
        self.spinbutton_tab_width.connect("value-changed", change_cb)
        self.spinbutton_indent_width.connect("value-changed", change_cb)
        self.spinbutton_right_margin.connect("value-changed", change_cb)
        self.spinbutton_font_size.connect("value-changed", change_cb)
        self.combobox_encoding.connect("changed", change_cb)
        self.combobox_separator.connect("changed", change_cb)
        self.combobox_font.connect("changed", change_cb)
        self.treeview_colourscheme_sel.connect("changed", change_cb)


    def reset(self):
        settings = self.editor.settings

        # various spin buttons
        self.spinbutton_tab_width.set_value(settings.tab_size)
        self.spinbutton_indent_width.set_value(settings.indent_width)
        self.spinbutton_right_margin.set_value(settings.right_margin)
        self.spinbutton_font_size.set_value(settings.font_size)

        # indent spaces
        self.checkbutton_indent_spaces.set_active(settings.indent_spaces)

        # encoding
        m = self.combobox_encoding.get_model()
        i = get_text_iter(m, settings.file_encoding)
        self.combobox_encoding.set_active_iter(i)

        # separator
        m = self.combobox_separator.get_model()
        i = get_text_iter(m, settings.linesep)
        self.combobox_separator.set_active_iter(i)

        # font
        m = self.combobox_font.get_model()
        i = get_text_iter(m, settings.font_name)
        self.combobox_font.set_active_iter(i)

        # colourscheme
        m = self.treeview_colourscheme.get_model()
        i = get_text_iter(m, settings.colourscheme)
        self.treeview_colourscheme_sel.select_iter(i)

    def show(self):
        self.reset()
        self.notebook.set_current_page(0)
        self.window.show_all()

class GtkFindDialog(object):
    def __init__(self, editor):
        self.editor = editor

        g = gtk.glade.XML(os.path.join(GLADE_DIR, 'find_replace.glade'))
        self.window = g.get_widget('window')
        self.window.set_title('Find and Replace')
        self.window.set_transient_for(self.editor.window)

        self.search_entry = g.get_widget('search_entry')
        self.replace_entry = g.get_widget('replace_entry')

        self.selection_radio = g.get_widget('selection_radio')
        self.current_radio = g.get_widget('current_radio')
        self.documents_radio = g.get_widget('documents_radio')
        self.workspace_radio = g.get_widget('workspace_radio')
        self.directory_radio = g.get_widget('directory_radio')

        self.workspace_fltr_combobox = g.get_widget('workspace_fltr_combobox')
        self.directory_entry = g.get_widget('directory_entry')
        self.choose_button = g.get_widget('choose_button')
        self.filter_entry = g.get_widget('filter_entry')

        self.find_button = g.get_widget('find_button')
        self.replace_button = g.get_widget('replace_button')
        self.close_button = g.get_widget('close_button')

        self.ignore_case_check = g.get_widget('ignore_case_check')
        self.regex_check = g.get_widget('regex_check')
        self.recursive_check = g.get_widget('recursive_check')
        self.skip_hidden_check = g.get_widget('skip_hidden_check')

         # TODO: save these in settings and load from there
        self.skip_hidden_check.set_active(True)
        self.recursive_check.set_active(True)

        self.is_first = True

        self.workspace_fltr_liststore = g.get_widget('workspace_filter')
         # type, pattern, name
        self.workspace_fltr_liststore = gtk.ListStore(str, str, str)
        self.workspace_fltr_combobox.set_model(self.workspace_fltr_liststore)
        cell = gtk.CellRendererText()
        self.workspace_fltr_liststore.clear()
        self.workspace_fltr_combobox.pack_start(cell, True)
        self.workspace_fltr_combobox.add_attribute(cell, 'text', 2)

        self.sync_workspace()

        def find_clicked(widget, *args):
            self.do_find()
        self.find_button.connect('clicked', find_clicked)

        def search_in_toggled(radio, *args):
            if radio.get_active():
                # skip the one that got untoggled
                self.sync_controls()

        self.selection_radio.connect('toggled', search_in_toggled)
        self.current_radio.connect('toggled', search_in_toggled)
        self.documents_radio.connect('toggled', search_in_toggled)
        self.workspace_radio.connect('toggled', search_in_toggled)
        self.directory_radio.connect('toggled', search_in_toggled)

        def window_delete_event(widget, event):
            self.window.hide()
            return True
        self.window.connect('delete_event', window_delete_event)

        # TODO: store previous directory in settings and load from there
        homedir = os.path.expanduser('~')+os.path.sep
        self.directory_entry.set_text(homedir)

        def choose_clicked(widget):
            dialog = gtk.FileChooserDialog("Choose Directory",
                                       self.editor.window,
                                       gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            dialog.set_default_response(gtk.RESPONSE_OK)
            #dialog.set_show_hidden(False)

            current_path = self.directory_entry.get_text()
            if os.path.exists(current_path):
                dialog.set_current_folder(current_path)
            else:
                homedir = os.path.expanduser('~')+os.path.sep
                dialog.set_current_folder(homedir)

            response = dialog.run()
            dialog.hide()

            if response == gtk.RESPONSE_OK:
                path = dialog.get_filename()
                path = path.decode(sys.getfilesystemencoding())
                path = path.encode('utf8')
                self.directory_entry.set_text(path)
            try:
                dialog.destroy()
            except AttributeError:
                pass
        self.choose_button.connect("clicked", choose_clicked)

        def entry_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Return':
                self.do_find()
                return True
            return False
        self.search_entry.connect("key-press-event", entry_keypress)

        def close_clicked(widget):
            self.window.hide()
        self.close_button.connect('clicked', close_clicked)

        def window_keypress(widget, event):
            keyname = gtk.gdk.keyval_name(event.keyval)
            if keyname == 'Escape':
                self.window.hide()
                return True
            return False
        self.window.connect("key-press-event", window_keypress)


    def sync_workspace(self):
        self.workspace_fltr_liststore.clear()
        self.workspace_fltr_liststore.append(['glob', '*', 'All Files'])
        self.workspace_fltr_combobox.set_active(0)

        workspace = self.editor.workspace

        if workspace:
            self.workspace_radio.props.sensitive = True
            self.workspace_fltr_combobox.props.sensitive = True
        else:
            if self.workspace_radio.get_active():
                self.workspace_radio.set_active(False)
                self.documents_radio.set_active(True)
            self.workspace_radio.props.sensitive = False
            self.workspace_fltr_combobox.props.sensitive = False

        if workspace:
            for name, pattern in workspace.filter_globs.iteritems():
                self.workspace_fltr_liststore.append(['glob', pattern, name])
            for name, pattern in workspace.filter_regulars.iteritems():
                self.workspace_fltr_liststore.append(['regex', pattern, name])

        self.sync_controls()

    def sync_controls(self):
        # enable / disable workspace widgets:
        if self.workspace_radio.get_active():
            self.workspace_fltr_combobox.props.sensitive = True
        else:
            self.workspace_fltr_combobox.props.sensitive = False

        # enable / disable directory widgets:
        if self.directory_radio.get_active():
            sensitive = True
        else:
            sensitive = False

        self.directory_entry.props.sensitive = sensitive
        self.choose_button.props.sensitive = sensitive
        self.filter_entry.props.sensitive = sensitive
        self.recursive_check.props.sensitive = sensitive

    def do_find(self):
        self.window.hide()

        if self.is_first:
            self.is_first = False
            height = self.editor.settings.win_height
            # there has to be a better way..
            self.editor.textarea.table.set_size_request(-1, height-250)

        search_pattern = self.search_entry.get_text()
        replace_pattern = self.replace_entry.get_text()

        if not search_pattern:
            # TODO: do bell or some other feedback
            return

        d = {
            'search': search_pattern,
            'replace': replace_pattern,
            'ignore_case': self.ignore_case_check.get_active(),
            'use_regex': self.regex_check.get_active(),
            'skip_hidden': self.skip_hidden_check.get_active()
        }

        if self.selection_radio.get_active():
            d['search_type'] = SEARCH_SELECTION
            d['view'] = self.editor.textarea.view

        elif self.current_radio.get_active():
            d['search_type'] = SEARCH_DOCUMENT
            d['view'] = self.editor.textarea.view

        elif self.documents_radio.get_active():
            d['search_type'] = SEARCH_DOCUMENTS

        elif self.workspace_radio.get_active():
            d['search_type'] = SEARCH_WORKSPACE
            d['workspace'] = self.editor.workspace

            i = self.workspace_fltr_combobox.get_active_iter()
            p_type = self.workspace_fltr_liststore.get_value(i, 0)
            p_name = self.workspace_fltr_liststore.get_value(i, 1)

            if p_type == 'glob':
                d['workspace_filter_glob'] = p_name
            else:
                d['workspace_filter_regex'] = p_name

        else:
            d['search_type'] = SEARCH_DIRECTORY
            d['directory'] = self.directory_entry.get_text()
            d['directory_filter'] = self.filter_entry.get_text()
            d['is_recursive'] = self.recursive_check.get_active()

        search = GtkSearch(self.editor, **d)
        self.editor.searches.append(search)
        self.editor.search = search

    def show(self):
        view = self.editor.textarea.view

        if view.selection:
            self.selection_radio.props.sensitive = True
            self.selection_radio.set_active(True)
        else:
            if self.selection_radio.get_active():
                self.current_radio.set_active(True)
            self.selection_radio.props.sensitive = False

        self.window.show_all()
        self.search_entry.grab_focus()
