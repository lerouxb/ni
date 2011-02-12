import sys, os, math, time

import gtk, gobject
import pango
from pygments.token import Token
from ni.actions.defaultactions import *
from ni.editors.gtk.utils import make_pango_layout, add_selection_to_layout
from ni.core.text import cap


# NOTE: Most actions are accessable from the menu and those form part of the
# actiongroups that gets set up in GTKEditor which maps those gtk.Action
# instances to ni Action classes. The only things that still need to go here
# are basic editing commands. Text input is handled by the input manager in
# the "on_im_commit" callback.
shortcuts = {
    'BACKSPACE': DeleteTextBackward,
    'DELETE': DeleteTextForward,
    'ESCAPE': CancelSelection,
    'CTRL+MINUS': ToggleDashComment,
    'CTRL+SHIFT+NUMBERSIGN': ToggleHashComment,
    'CTRL+SLASH': ToggleSlashComment,
    'CTRL+SHIFT+ASTERISK': BlockComment
}
sel_shortcuts = {
    'UP': MoveCursorUp,
    'DOWN': MoveCursorDown,
    'LEFT': MoveCursorLeft,
    'RIGHT': MoveCursorRight,
    'CTRL+LEFT': MoveCursorWordLeft,
    'CTRL+RIGHT': MoveCursorWordRight,
    'PAGE_UP': MoveCursorPageUp,
    'PAGE_DOWN': MoveCursorPageDown,
    'HOME': MoveCursorLineStart,
    'END': MoveCursorLineEnd,
    'CTRL+HOME': MoveCursorStart,
    'CTRL+END': MoveCursorEnd,
    'CTRL+GRAVE': SwitchToRecentDocument    
}

class GTKTextarea(object):
    def __init__(self, editor):
        # TODO: this should come from config

        self.editor = editor # circular reference..

        self.gutter_line_width = 2
        self.gutter_line_gap = 4

        self.table = gtk.Table(2, 2, False)

        self.drawingarea = gtk.DrawingArea()
        self.drawingarea.set_double_buffered(False)
        self.drawingarea.set_flags(gtk.CAN_FOCUS|gtk.HAS_FOCUS|gtk.CAN_DEFAULT|gtk.HAS_DEFAULT|gtk.APP_PAINTABLE|gtk.SENSITIVE|gtk.PARENT_SENSITIVE)
        self.drawingarea.set_events(gtk.gdk.POINTER_MOTION_MASK|gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.BUTTON_RELEASE_MASK|gtk.gdk.KEY_PRESS_MASK|gtk.gdk.KEY_RELEASE_MASK|gtk.gdk.SCROLL_MASK)
        self.drawingarea.connect("expose_event",
                                 self.on_drawingarea_expose_event)
        self.drawingarea.connect("motion_notify_event",
                                 self.on_drawingarea_motion_notify_event)
        self.drawingarea.connect("button_press_event",
                                 self.on_drawingarea_button_press_event)
        self.drawingarea.connect("button_release_event",
                                 self.on_drawingarea_button_release_event)
        self.drawingarea.connect("key_press_event",
                                 self.on_drawingarea_key_press_event)
        self.drawingarea.connect("scroll_event",
                                 self.on_drawingarea_scroll_event)
        self.drawingarea.connect("size_allocate",
                                 self.on_drawingarea_size_allocate)

        self.gc = None
        self.pixmap = None
        self.width = None
        self.height = None
        self.pl = None

        # TODO: this should be in config
        self.scroll_inc = 3

        self.hadjustment = gtk.Adjustment(value=0, lower=0, upper=0,
                                          step_incr=self.scroll_inc,
                                          page_incr=1, page_size=1)
        self.hadjustment.connect("changed", self.on_adjustment_changed)
        self.hadjustment.connect("value-changed",
                                 self.on_adjustment_value_changed)
        self.vadjustment = gtk.Adjustment(value=0, lower=0, upper=0,
                                          step_incr=self.scroll_inc,
                                          page_incr=1, page_size=1)
        self.vadjustment.connect("changed", self.on_adjustment_changed)
        self.vadjustment.connect("value-changed",
                                 self.on_adjustment_value_changed)

        self.hscrollbar = gtk.HScrollbar(self.hadjustment)
        self.vscrollbar = gtk.VScrollbar(self.vadjustment)

        #(child, left_attach, right_attach, top_attach, bottom_attach,
        # xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL,
        # xpadding=0, ypadding=0)
        self.table.attach(self.drawingarea, 0, 1, 0, 1,
                          gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND)
        self.table.attach(self.hscrollbar, 0, 1, 1, 2,
                          gtk.FILL, gtk.FILL)
        self.table.attach(self.vscrollbar, 1, 2, 0, 1,
                          gtk.FILL, gtk.FILL)

        self.mouse_selection_start = None

        self.hscrollbar_visible = True

    def attach(self, method):
        method(self.table)

        # only set the font after things are "realized"
        font_name = self.editor.settings.font_name
        font_size = self.editor.settings.font_size
        self.set_font('%s %s' % (font_name, font_size))

    def show(self):
        # TODO: move to view, take mode into account, use Colourscheme object
        #self.colours = get_colours(self.drawingarea)

        self.im = gtk.IMContextSimple()
        self.im.set_client_window(self.drawingarea.window)
        self.im.set_use_preedit(True)
        self.im.connect("commit", self.on_im_commit)
        self.im.focus_in()
        self.im.reset()

        self.is_cursor_visible = True
        def toggle_cursor():
            self.is_cursor_visible = not self.is_cursor_visible
            self.draw_cursor()
            return True
        gobject.timeout_add(1000, toggle_cursor)

        self.drawingarea.grab_focus()


    ### Properties

    def get_gutter_char_width(self):
        num_lines = self.view.document.num_lines
        return max(5, len(str(num_lines)))
    gutter_char_width = property(get_gutter_char_width)

    def get_gutter_width(self):
        extra = self.gutter_line_width + self.gutter_line_gap
        return self.gutter_char_width*self.char_width+extra
    gutter_width = property(get_gutter_width)

    ### Textarea methods

    def get_textbox_dimensions(self):
        if self.editor.settings.show_gutter:
            xoffset = self.gutter_width
        else:
            xoffset = 0

        width, height = self.drawingarea.window.get_size()
        num_chars = int(math.ceil((width-xoffset)*1.0/self.char_width))
        num_lines = int(math.ceil(height*1.0/self.char_height))
        return num_chars, num_lines
    textbox_dimensions = property(get_textbox_dimensions)

    def get_textbox_text_clip(self):
        if self.editor.settings.show_gutter:
            xoffset = self.gutter_width
        else:
            xoffset = 0

        width, height = self.drawingarea.window.get_size()
        return (0, xoffset), (width-xoffset, height)
    textbox_text_clip = property(get_textbox_text_clip)

    def get_page_size(self):
        width, height = self.textbox_dimensions
        return width-1, height-1
    page_size = property(get_page_size)

    ### GTKTextarea specifics

    def set_font(self, desc):
        """Set self.font, self.char_width and self.char_height."""

        # TODO: This only works with monospace fonts. Because we use char_width
        # and char_height all over the place, we'll have to make big changes
        # all over to support variable width fonts. Not really a priority,
        # because this is supposed to be a code editor anyway..

        self.font = pango.FontDescription(desc)

        pl = self.drawingarea.create_pango_layout("A")
        pl.set_font_description(self.font)
        self.char_width, self.char_height = pl.get_pixel_size()

        # when the font is set or changes, then the character size changes, 
        # therefore the textbox dimensions (in number of chars) changes, 
        # so the number of chars on screen in each dimension changes, so we
        # have to adjust the scrollbars
        self.adjust_adjustments()

    def sync_scroll_pos(self):
        """
        Set scrollbar scroll positions to view's scroll_pos. 
        Use wherever we (might have) changed view.scroll_pos.
        """
        
        yoffset, xoffset = self.view.scroll_pos
        if int(self.hadjustment.value) != xoffset:
            self.hadjustment.set_value(xoffset)
        if int(self.vadjustment.value) != yoffset:
            self.vadjustment.set_value(yoffset)

    def adjust_adjustments(self):
        """
        Set the ranges of the horizontal and vertical scrollbars, hide 
        scrollbars if they aren't necessary.
        """

        view = self.view
        doc = view.document

        # TODO: it must be possible to optimise this so that we don't have to
        # loop through lines
        total_chars = 0
        for i in xrange(doc.num_lines):
            line_length = len(doc.get_line(i))
            if line_length > total_chars:
                total_chars = line_length

        total_lines = doc.num_lines

        # erm... why +2? something to do with two scrollbars?
        last_char = total_chars + 2
        last_line = total_lines + 2

        # set the adjustments to be as wide as the widest line and as long as
        # the number of lines
        if self.hadjustment.upper != last_char:
            self.hadjustment.upper = last_char
        if self.vadjustment.upper != last_line:
            self.vadjustment.upper = last_line

        # the rest needs the window to be initialised so we can get the 
        # dimensions
        if not self.drawingarea.window:
            return

        num_chars, num_lines = self.textbox_dimensions

        #scrolly, scrollx = view.scroll_pos

        # set the page increments to be a screen-ful at a time
        if self.hadjustment.page_increment != num_chars:
            self.hadjustment.page_increment = num_chars-1
            self.hadjustment.page_size = num_chars
        if self.vadjustment.page_increment != num_lines:
            self.vadjustment.page_increment = num_lines-1
            self.vadjustment.page_size = num_lines

        self.editor.update_status()

        if num_chars >= last_char:
            if self.hscrollbar_visible:
                self.hadjustment.value = 0
                self.hscrollbar.hide()
                self.hscrollbar_visible = False
        else:
            if not self.hscrollbar_visible:
                self.hscrollbar.show()
                self.hscrollbar_visible = True

    def draw_background(self):
        """Draw everything that's not the text or selection.
        """

        widget = self.drawingarea
        draw_target = self.pixmap
        view = self.view
        doc = view.document
        cursor_y, cursor_x = view.cursor_pos
        width, height = widget.window.get_size()
        xoffset = int(self.hadjustment.value)
        yoffset = int(self.vadjustment.value)
        chars = int(self.hadjustment.page_size)
        rows = int(self.vadjustment.page_size)
        clip_off, clip_size = self.textbox_text_clip
        clip_yoff, clip_xoff = clip_off
        clip_width, clip_height = clip_size

        colours = view.colours

        if view.selection:
            selection = view.selection.get_normalised()
        else:
            selection = None

        gutter_char_width = self.gutter_char_width
        gutter_width = self.gutter_width

        # clear the background
        if self.editor.settings.show_gutter:
            bg_x = gutter_width-self.gutter_line_gap/2
            bg_w = width-bg_x
        else:
            bg_x = 0
            bg_w = width

        draw_target.draw_rectangle(colours['bg']['gc'], True,
                                   bg_x, 0,
                                   bg_w, height)

        # is the current line on screen?
        cline_onscreen = cursor_y >= yoffset and cursor_y < yoffset+rows

        # do we have a selection and is the line inside it?
        line_in_selection = (selection and \
            selection.line_in_selection(cursor_y, normalised=True))

        if cline_onscreen and not line_in_selection:
            # draw the current line's background
            start_x = gutter_width-self.gutter_line_gap/2
            start_y = (cursor_y-yoffset)*self.char_height

            draw_target.draw_rectangle(colours['current']['gc'], True,
                                       start_x, start_y,
                                       clip_width, self.char_height)

        if self.editor.settings.show_gutter:
            gutter_bg_width = gutter_width-self.gutter_line_gap/2
            draw_target.draw_rectangle(colours['gutter_bg']['gc'], True,
                                       0, 0,
                                       gutter_bg_width, height)

            # draw the gutter line
            line_x = gutter_width-self.gutter_line_width-self.gutter_line_gap/2
            draw_target.draw_rectangle(colours['gutter_line']['gc'], True,
                                       line_x, 0,
                                       self.gutter_line_width, height-1)

            # gutter
            num_lines = doc.num_lines
            y = 0
            for line_num in xrange(yoffset+1, yoffset+rows+1):
                if line_num > num_lines:
                    break
                format = '%'+str(gutter_char_width)+'d'
                pl = widget.create_pango_layout(format % (line_num,))
                pl.set_font_description(self.font)
                if line_num-1 == cursor_y:
                    gc = colours['gutter_current']['gc']
                else:
                    if line_num % 5:
                        gc = colours['gutter_plain']['gc']
                    else:
                        gc = colours['gutter_fifth']['gc']
                draw_target.draw_layout(gc, 0, y, pl)
                y += self.char_height

    def draw_text(self):
        """Draw the highlighted pango text."""

        widget = self.drawingarea
        draw_target = self.pixmap
        view = self.view
        offset = (            
            int(self.vadjustment.value),
            int(self.hadjustment.value),
        )
        yoffset, xoffset = offset
        size = (
            int(self.hadjustment.page_size),
            int(self.vadjustment.page_size)
        )
        clip_off, clip_size = self.textbox_text_clip
        clip_yoff, clip_xoff = clip_off
        width, height = widget.window.get_size()
        colours = view.colours

        doc = view.document

        #must_relex = bool(doc.relex_from)
        if not self.pl or doc.must_relex:
            #print "recalculating pango layout.."

            doc.update_tokens(view.scroll_pos, view.textbox_dimensions)

            tab_size = self.editor.settings.tab_size
            self.pl = make_pango_layout(view)
            self.pl.set_font_description(self.font)

        if view.selection:
            pl = self.pl.copy()
            selection = view.selection
            add_selection_to_layout(pl, colours, doc, selection, offset, size)

        else:
            pl = self.pl

        colour = colours['plain']['gc']
        draw_target.draw_layout(colour, clip_xoff, 0, pl)

        if self.editor.settings.show_margin:
            rm = self.editor.settings.right_margin

            # HACK: 2 is a magic number. Looks like self.char_width is not
            # perfectly accurate and with long lines the characters don't all
            # line up pixel-perfectly as a multiple of char_width.
            guide_x = rm*self.char_width - xoffset*self.char_width - 2

            # draw the guide line
            draw_target.draw_line(colours['guide']['gc'],
                                  guide_x, 0,
                                  guide_x, height-1)


    def draw_cursor(self):
        # this is a bit of a hack to stop things from being drawn before we
        # properly set things up
        if not self.drawingarea.window:
            return

        view = self.view
        doc = view.document

        cy, cx = self.view.cursor_pos
        line = doc.get_line(cy)
        cx = char_pos_to_tab_pos(line, cx, doc.tab_size)

        clip_off, clip_size = self.textbox_text_clip
        clip_yoff, clip_xoff = clip_off
        clip_width, clip_height = clip_size

        xoffset = int(self.hadjustment.value)
        yoffset = int(self.vadjustment.value)
        chars = int(self.hadjustment.page_size)
        rows = int(self.vadjustment.page_size)

        y = cy-yoffset
        ypos = y*self.char_height

        if cx >= xoffset and cx < xoffset+chars and \
        cy >= yoffset and cy < yoffset+rows:
           # redraw background if the cursor is on screen
           self.drawingarea.window.draw_drawable(self.gc, self.pixmap,
                                                 0, ypos,
                                                 0, ypos,
                                                 self.width, self.char_height)
        else:
            return # cursor outside of bounds

        if self.is_cursor_visible and self.editor.window.is_active():
            gc = view.colours['plain']['gc']
        else:
            # the cursor is not visible, so just return
            return

        x = cx-xoffset
        xpos = clip_xoff+x*self.char_width
        # HACK: 2 is a magic number
        self.drawingarea.window.draw_rectangle(gc, True,
                                               xpos, ypos,
                                               2, self.char_height)

    def draw_brackets(self):
        view = self.view
        doc = view.document

        if view.brackets == None:
            view.calculate_brackets()

        if not view.brackets:
            return

        draw_target = self.pixmap

        xoffset = int(self.hadjustment.value)
        yoffset = int(self.vadjustment.value)

        chars = int(self.hadjustment.page_size)
        rows = int(self.vadjustment.page_size)

        clip_off, clip_size = self.textbox_text_clip
        clip_yoff, clip_xoff = clip_off
        clip_width, clip_height = clip_size

        cursor_pos = view.cursor_pos

        gc = draw_target.new_gc()
        gc.copy(view.colours['plain']['gc'])
        #gc.set_function(gtk.gdk.INVERT)

        screen_start = (xoffset, yoffset)
        lastline_num = min(doc.num_lines-1, yoffset+rows-1)
        screen_end = (chars, lastline_num)

        for bracket_offset in view.brackets:
            bracket_pos = doc.offset_to_cursor_pos(bracket_offset)
            if min(bracket_pos, screen_start) == screen_start and\
            min(bracket_pos, screen_end) == bracket_pos:
                y, x = bracket_pos
                line = doc.get_line(y)
                x = char_pos_to_tab_pos(line, x, doc.tab_size)
                x -= xoffset
                y -= yoffset

                if x >= 0 and x < chars and y >= 0 and y < rows:
                    xpos = clip_xoff+x*self.char_width
                    ypos = y*self.char_height
                    draw_target.draw_rectangle(gc,
                                               False,
                                               xpos,
                                               ypos,
                                               self.char_width,
                                               self.char_height)
            
            # c for cursor, b for bracket
            cy, cx = cursor_pos
            by, bx = bracket_pos
            
            if cy != by:
                # s for start, b for end
                if cy < by:
                    sy = cy
                    ey = by
                else:
                    sy = by
                    ey = cy

                # cap them (c for capped)
                csy = cap(sy, yoffset, yoffset+rows-1)
                cey = cap(ey, yoffset, yoffset+rows-1)

                # d for draw
                dsy = csy - yoffset
                dey = cey - yoffset

                gc = view.colours['gutter_line']['gc']

                # l for line
                lx = self.char_width/2-2
                if sy == csy:
                    ly = dsy*self.char_height+self.char_height/2-2
                    # start arrow
                    draw_target.draw_rectangle(gc, True, lx, ly, 8, 4)
                    lh = (dey-dsy)*self.char_height
                else:
                    ly = dsy*self.char_height
                    if ey == cey:
                        lh = (dey-dsy)*self.char_height+self.char_height/2-2
                    else:
                        lh = (dey-dsy)*self.char_height

                # vertical line
                draw_target.draw_rectangle(gc, True, lx, ly, 4, lh)

                if ey == cey:
                    # end angle
                    y = dey*self.char_height+self.char_height/2-2
                    draw_target.draw_rectangle(gc, True, lx, y, 8, 4)

    def draw(self):
        # this is a bit of a hack to stop things from being drawn before we
        # properly set things up
        if not self.pixmap or not self.drawingarea.window:
            return

        # there has got to be a better way..
        if self.view.just_switched:
            self.view.calculate_brackets()
            self.view.just_switched = False

        self.draw_background()

        self.draw_text()

        self.draw_brackets()

        self.drawingarea.window.draw_drawable(self.gc,
                                              self.pixmap,
                                              0, 0,
                                              0, 0,
                                              self.width, self.height)

        self.draw_cursor()

    def redraw(self):
        self.pl = None
        self.drawingarea.queue_draw()

    def hscroll(self, direction):
        """Adjust self.hadjustment.

        Scrolling happens in different places due to the different events. This
        is just the common code for scrolling horisontally.
        """

        xoffset = int(self.hadjustment.value)
        yoffset = int(self.hadjustment.value)

        chars = int(self.hadjustment.page_size)
        rows = int(self.vadjustment.page_size)

        if direction > 0:
            maximum = int(self.hadjustment.upper-chars)
            if maximum < 0:
                maximum = 0
        else:
            maximum = 0

        value = int(self.hadjustment.value)

        if direction > 0 and value+self.scroll_inc >= maximum:
            self.hadjustment.set_value(maximum)
        elif direction < 0 and value-self.scroll_inc < 0:
            self.hadjustment.set_value(0)
        else:
            self.hadjustment.set_value(value+direction*self.scroll_inc)

    def vscroll(self, direction):
        """Adjust self.vadjustment.

        Scrolling happens in different places due to the different events. This
        is just the common code for scrolling vertically.

        See on_drawingarea_motion_notify_event() and
        on_drawingarea_scroll_event().
        """

        xoffset = int(self.vadjustment.value)
        yoffset = int(self.vadjustment.value)

        chars = int(self.hadjustment.page_size)
        rows = int(self.vadjustment.page_size)

        if direction > 0:
            maximum = int(self.vadjustment.upper-rows)
            if maximum < 0:
                maximum = 0
        else:
            maximum = 0

        value = int(self.vadjustment.value)

        if direction > 0 and value+self.scroll_inc >= maximum:
            self.vadjustment.set_value(maximum)
        elif direction < 0 and value-self.scroll_inc < 0:
            self.vadjustment.set_value(0)
        else:
            self.vadjustment.set_value(value+direction*self.scroll_inc)

    ### InputManager callbacks

    def on_im_commit(self, im, string):
        """Add unicode text entered on the drawingarea to the view.

        This handles the input manager for the main editing area's callbacks.
        The input manager figures out what text was input after compose keys
        and all that got taken into consideration. It handles all those
        multi-key characters in gtk / gnome and all that. It is a very poorly
        documented area of pygtk. See self.im which gets set up in show().
        Also check out on_drawingarea_key_press_event() which actually passes
        the key presses in to the input manager in order to "filter" keys.
        """

        action = InsertText(self.view, string)
        self.view.execute_action(action)

    ### DrawingArea callbacks

    def on_drawingarea_expose_event(self, widget, event):
        self.draw()

    def on_drawingarea_size_allocate(self, widget, allocation):
        if self.drawingarea.window:
            # only do this if things are properly realized

            if not self.gc:
                self.gc = self.drawingarea.window.new_gc()

            self.pl = None # window got resized, so the text layout is invalid

            self.width = allocation.width
            self.height = allocation.height
            self.pixmap = gtk.gdk.Pixmap(self.drawingarea.window,
                                         self.width, self.height)

            # when the drawingarea changes in size, the page size for the 
            # scrollbars change (which affects the size of the drag handle 
            # thing) so the scrollbars need to be adjusted
            self.adjust_adjustments()

    def on_drawingarea_button_press_event(self, widget, event):
        if not widget.is_focus():
            widget.grab_focus()

        if event.type == gtk.gdk._2BUTTON_PRESS:
            # double-click
            self.view.execute_action(SelectWord(self.view))
            return True

        doc = self.view.document

        xoffset = int(self.hadjustment.value)
        yoffset = int(self.vadjustment.value)

        clip_off, clip_size = self.textbox_text_clip
        clip_yoff, clip_xoff = clip_off
        clip_width, clip_height = clip_size

        x, y = event.x, event.y
        if x < clip_xoff:
            # user clicked somewhere in the gutter
            return True
        x -= clip_xoff

        last_line = doc.num_lines-1 # why last_line and not num_lines?
        clicked_yoffset = int(y / self.char_height)+yoffset
        ychar = min(last_line, clicked_yoffset)

        line_width = len(doc.get_line(ychar))
        clicked_xoffset = int(round(x / self.char_width))+xoffset
        xchar = min(line_width, clicked_xoffset)

        if ychar < 0:
            # if you click somewhere and the file is empty, then this might end
            # up to be -1 which is just dodgy
            return True

        self.view.selection = None

        self.view.execute_action(MoveCursor(self.view, (ychar, xchar)))

        self.mouse_selection_start = (ychar, xchar)

        return True

    def on_drawingarea_motion_notify_event(self, widget, event):
        x, y = event.x, event.y
        width, height = widget.window.get_size()
        xoffset = int(self.hadjustment.value)
        yoffset = int(self.vadjustment.value)

        clip_off, clip_size = self.textbox_text_clip
        clip_yoff, clip_xoff = clip_off
        clip_width, clip_height = clip_size

        if x < clip_xoff:
            widget.window.set_cursor(None)

        else:
            widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))

        # make / extend the selection if the mouse is being held down
        start = self.mouse_selection_start
        if start:
            view = self.view
            doc = view.document

            chars = int(self.hadjustment.page_size)
            rows = int(self.vadjustment.page_size)

            mouse_yoffset = int(y / self.char_height)+yoffset
            num_lines = doc.num_lines # why num_lines and not last_line?
            ychar = min(num_lines, mouse_yoffset)

            line_length = len(doc.get_line(ychar))
            mouse_xoffset = int(round((x-clip_xoff) / self.char_width))+xoffset
            xchar = min(line_length, mouse_xoffset)

            if ychar < 0:
                ychar = 0

            if xchar < xoffset:
                xchar = xoffset
            if x < clip_xoff:
                self.hscroll(-1)

            if xchar > chars+xoffset:
                xchar = chars+xoffset
            if x > width:
                self.hscroll(1)

            if ychar < yoffset:
                ychar = yoffset
            if y < 0:
                self.vscroll(-1)

            if ychar > rows+yoffset:
                ychar = rows+yoffset
            if y > height:
                self.vscroll(1)

            end = (ychar, xchar)

            if end != start:
                start_offset = doc.cursor_pos_to_offset(start)
                end_offset = doc.cursor_pos_to_offset(end)
                view.selection = Selection(doc, start_offset, end_offset)
                self.editor.selection_actiongroup.set_sensitive(True)
                view.cursor_pos = (ychar, xchar)
                self.is_cursor_visible = True
                self.drawingarea.queue_draw()

        return True

    def on_drawingarea_button_release_event(self, widget, event):
        # TODO: drop? end selection?

        self.mouse_selection_start = None

        return True

    def on_drawingarea_key_press_event(self, widget, event):
        if not self.im.filter_keypress(event):
            keyval = event.keyval
            keyname = gtk.gdk.keyval_name(keyval)
            state = event.state

            keys = []

            is_control = False
            is_alt = False
            is_super = False
            is_shift = False

            if state & gtk.gdk.CONTROL_MASK:
                is_control = True
                keys.append('Ctrl')
            if state & gtk.gdk.MOD1_MASK:
                is_alt = True
                keys.append('Alt')
            if state & gtk.gdk.MOD4_MASK:
                is_super = True
                keys.append('Super')
            if state & gtk.gdk.SHIFT_MASK:
                is_shift = True
                keys.append('Shift')

            keys.append(keyname)
            shortcut = ('+'.join(keys)).upper()
            
            if shortcut == 'RETURN':
                action = InsertText(self.view, '\n')

            elif shortcut == 'TAB':
                settings = self.editor.settings
                if settings.indent_spaces:
                    spaces = ' '*settings.indent_width
                    action = InsertText(self.view, spaces)
                else:
                    action = InsertText(self.view, '\t')

            else:
                if shortcuts.has_key(shortcut):
                    action = shortcuts[shortcut](self.view)
                else:
                    if is_shift:
                        keys.remove('Shift')
                    sel_shortcut = ('+'.join(keys)).upper()

                    if not sel_shortcuts.has_key(sel_shortcut):
                        return False

                    ActionClass = sel_shortcuts[sel_shortcut]
                    if issubclass(ActionClass, MoveCursorAction):
                        if not is_shift:
                            self.view.selection = None
                            action_group = self.editor.selection_actiongroup
                            action_group.set_sensitive(False)
                        action = ActionClass(self.view, is_shift)
                    else:
                        action = ActionClass(self.view)

            self.view.execute_action(action)

            # TODO: figure out what happens to menu keyboard shortcuts..

        return True

    def on_drawingarea_scroll_event(self, widget, event):
        # This event gets generated if/when you scroll using the mouse wheel.

        if event.direction == gtk.gdk.SCROLL_UP:
            self.vscroll(-1)

        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.vscroll(1)

        return True

    ### Adjustment callbacks
    def on_adjustment_changed(self, adjustment):
        xoffset = int(self.hadjustment.value)
        yoffset = int(self.vadjustment.value)
        self.view.scroll_pos = (yoffset, xoffset)

    def on_adjustment_value_changed(self, adjustment):
        # Store the scroll position inside the document so that we can go back
        # to it when we switch back to it later.
        self.view.scroll_pos = (int(self.vadjustment.value), 
                                int(self.hadjustment.value))
        self.redraw() # this should clear self.pl

