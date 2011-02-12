import os
import gtk
import gtk.glade
import pango
from ni.core.selection import Selection
from ni.editors.base.search import *


# add some event handlers for the tabs here
# how do we delete? remove the tab and then just remove from editor.searches?

class GtkSearch(Search):
    #def __init__(self, model, notebook, **kwargs):
    def __init__(self, editor, **kwargs):
        super(GtkSearch, self).__init__(editor, **kwargs)

        #self.model = model
        self.notebook = editor.search_notebook

        # hbox is the 'tab label'
        self.hbox = gtk.HBox(False)

        self.label = gtk.Label("Searching...")
        self.label.show()

        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_CLOSE, 1)

        self.button = gtk.Button()
        self.button.set_relief(gtk.RELIEF_NONE)
        self.button.set_image(self.image)
        self.button.show()

        self.hbox.pack_start(self.label)
        self.hbox.pack_end(self.button)

        # scrolledwindow is the 'tab content'
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)

        def num_func(column, cell, model, itr):
            num = model.get_value(itr, 0)

            if num != -1:
                # match
                cell.set_property('text', str(num+1))
                cell.set_property('visible', True)
            else:
                # folder (not visible)
                cell.set_property('text', '')
                cell.set_property('visible', False)

        def line_func(column, cell, model, itr):
            attributes = pango.AttrList()
            num = model.get_value(itr, 0)

            start = model.get_value(itr, 3)
            end = model.get_value(itr, 4)

            if num != -1:
                # match (monospaced font)
                cell.set_property('font', 'DejaVu Sans Mono 10')
                cell.set_property('weight', 400)

                #path = model.get_path(itr)
                #if self.treeview.get_selection().path_is_selected(path):
                if not self.treeview.get_selection().iter_is_selected(itr):
                    # HACK! This will surely look nasty in dark themes.
                    # should be rougly FFFF99 (bright yellow)
                    r = 65535
                    g = 65535
                    b = 36864
                    attr = pango.AttrBackground(r, g, b,
                                                start_index=start,
                                                end_index=end)
                    attributes.insert(attr)
            else:
                # folder (bold)
                cell.set_property('font', None)
                cell.set_property('weight', 800)

            cell.set_property('attributes', attributes)

        # linenum, path, line, start, end
        model = gtk.TreeStore(int, str, str, int, int)

        view = gtk.TreeView(model)
        view.set_headers_visible(False)
        view.unset_flags(gtk.CAN_FOCUS)

        column = gtk.TreeViewColumn('Match')

        cell_num = gtk.CellRendererText()
        cell_num.set_property('xalign', 1)
        cell_num.set_property('yalign', 0)
        column.pack_start(cell_num, False)
        #column.add_attribute(cell_num, 'text', 0)
        column.set_cell_data_func(cell_num, num_func)

        cell_line = gtk.CellRendererText()
        cell_line.set_property('xalign', 0)
        cell_line.set_property('yalign', 0)
        column.pack_end(cell_line, True)
        column.add_attribute(cell_line, 'text', 2)
        column.set_cell_data_func(cell_line, line_func)

        view.append_column(column)

        self.treemodel = model
        self.treeview = view

        self.scrolled_window.add(self.treeview)

        n = self.notebook.append_page(self.scrolled_window, self.hbox)
        self.notebook.show_all()
        self.notebook.set_current_page(n)

        def close_clicked(widget, *args):
            self.editor.cancel_search(self)
        self.button.connect('clicked', close_clicked)

        def jump(treeview, model, itr):
            #linenum, path, line, start, end
            linenum = model.get_value(itr, 0)
            filepath = model.get_value(itr, 1)
            line = model.get_value(itr, 2)
            start = model.get_value(itr, 3)
            end = model.get_value(itr, 4)

            #print linenum, filepath, line, start, end

            pos = (0, linenum)
            start_pos = increase_pos(pos, line[:start])
            end_pos = increase_pos(pos, line[:end])

            #print start_pos, end_pos

            view = None
            for v in self.editor.views:
                if filepath[0] == os.path.sep: # root
                    if v.document.location == filepath:
                        view = v
                        self.editor.switch_current_view(v)
                        break
                else:
                    # unsaved file
                    if v.document.title == filepath:
                        view = v
                        self.editor.switch_current_view(v)
                        break

            else:
                # sanity check so we don't try and open an in-memory file
                # that's never been saved to disk
                if filepath[0] == os.path.sep:
                    view = self.editor.new_view(filepath)
                else:
                    return

            view.brackets = None
            view.textarea.pl = None
            view.cursor_pos = end_pos
            view.selection = Selection(view.document, start_pos, end_pos)            
            #view.textarea.sync_scroll_pos() # is this necessary?
            #view.textarea.adjust_adjustments() # is this necessary?
            view.check_cursor()
            view.sync_selection()
            view.textarea.redraw()

        def treeview_row_activated(treeview, path, view_column):
            #self.editor.textarea.drawingarea.grab_focus()

            if len(path) == 2:
                # this means we're on a child row (ie result)
                #print treeview, path, view_column
                model = treeview.get_model()
                itr = model.get_iter(path)
                jump(treeview, model, itr)
        self.treeview.connect('row-activated', treeview_row_activated)

        def treeview_cursor_changed(treeview):
            #self.editor.textarea.drawingarea.grab_focus()

            model, itr = treeview.get_selection().get_selected()
            if itr:
                pitr = model.iter_parent(itr)
                if pitr:
                    # this iter has a parent, so it must be a result
                    jump(treeview, model, itr)
        self.treeview.connect('cursor-changed', treeview_cursor_changed)

        self.thread = InitialSearchThread()
        self.thread.start(self)

    def get_filename_itr(self, filename, create=True):
        store = self.treemodel

        nitr = None
        itr = store.get_iter_first()
        if itr:
            while itr:
                path = store.get_value(itr, 1)
                if path == filename:
                    return itr # short circuit
                    #nitr = itr
                    #break

                if path > filename:
                    # we went too far, so insert before
                    row = [-1, filename, filename, 0, 0]
                    nitr = store.insert_before(None, itr, row)
                    break

                itr = store.iter_next(itr)

        if not nitr:
            # append one at the end
            nitr = store.append(None, [-1, filename, filename, 0, 0])

        return nitr

    def clear_lines(self, filename, fromline):
        store = self.treemodel

        if fromline == 0:
            itr = store.get_iter_first()
            while itr:
                path = store.get_value(itr, 1)
                if path == filename:
                    store.remove(itr)
                    return
                else:
                    itr = store.iter_next(itr)

        else:
            itr = self.get_filename_itr(filename, False)
            if itr:
                citr = store.iter_children(itr)
                while citr:
                    linenum = store.get_value(citr, 0) #line number
                    if linenum >= fromline:
                        store.remove(citr)
                    else:
                        citr = store.iter_next(itr)

    def add_match(self, filename, match, linenum, start, end):
        # Do stuff here
        # int, str, str, int, int, int, int (linenum, path, line, start, end)

        store = self.treemodel

        pitr = self.get_filename_itr(filename)
        nitr = store.append(pitr, [linenum, filename, match, start, end])

        # expand the new row
        path = store.get_path(pitr)
        self.treeview.expand_row(path, True)

    def notify_done(self):
        self.label.set_use_markup(True)
        self.label.set_markup('Results for <i>%s</i>' % (self.search_pattern,))

    def detach(self):
        self.interrupt()

        n = self.notebook.page_num(self.scrolled_window)
        self.notebook.remove_page(n)
        if not self.notebook.get_n_pages():
            self.notebook.hide()

