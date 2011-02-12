import pango
from pygments.token import Token
import time
from ni.core.text import pad, cap, char_pos_to_tab_pos


def get_gtk_colours(widget, colourscheme, mode):
    colormap = widget.get_colormap()
    colours = colourscheme.get_colours_for_mode(mode)
    for c in colours.values():
        c['gdk'] = colormap.alloc_color(c['hex'])
        c['pango'] = pango.Color(c['hex'])
        c['gc'] = widget.window.new_gc(foreground=c['gdk'])
    return colours

class memoized(object):
   """Decorator that caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned, and
   not re-evaluated.
   """
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         self.cache[args] = value = self.func(*args)
         return value
      except TypeError:
         # uncachable -- for instance, passing a list as an argument.
         # Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      """Return the function's docstring."""
      return self.func.__doc__

@memoized
def get_style_for_ttype(ttype):
    # Not a dictionary because order matters and we use 'in' to test subsets,
    # we don't check if things match exactly. There are many more possible
    # tokens and new ones can always be defined, so we have to check subsets.
    # That makes this function fairly slow.. but we need it to map Tokens to
    # actual colours in the colourscheme..

    if ttype in Token.Text:
        return 'plain'
    if ttype in Token.Punctuation:
        return 'punctuation'
    if ttype in Token.Name.Function:
        return 'function'
    if ttype in Token.Name.Class:
        return 'class'
    if ttype in Token.Name.Builtin.Pseudo.Self:
        return 'self'
    if ttype in Token.Name.Builtin.Pseudo:
        return 'pseudo'
    if ttype in Token.Name.Builtin:
        return 'builtin'
    if ttype in Token.Name.Exception:
        return 'exception'
    if ttype in Token.Name.Tag:
        return 'tag'
    if ttype in Token.Name.Attribute:
        return 'attribute'
    if ttype in Token.Name:
        return 'name'
    if ttype in Token.Operator.Word:
        return 'wordoperator'
    if ttype in Token.Operator:
        return 'symboloperator'
    if ttype in Token.Keyword:
        return 'keyword'
    if ttype in Token.Literal.Number:
        return 'number'
    if ttype in Token.Literal:
        return 'literal'
    if ttype in Token.Comment:
        return 'comment'
    if ttype in Token.Error:
        return 'error'
    if ttype in Token.Other:
        return 'other'
    if ttype in Token.Generic:
        return 'generic'

    return 'plain'

def line_tokens(tokens, tab_size):
    tab_spaces = tab_size*' '

    line_tokens = []
    for ttype, value in tokens:
        lines = value.split('\n')
        for n, line in enumerate(lines):
            if n > 0:
                yield line_tokens
                line_tokens = []
            line_tokens.append((ttype, len(line.replace('\t', tab_spaces))))
    yield line_tokens

def clipped_tokens(token_lines, xoffset, num_chars):
    for token_line in token_lines:
        line_pos = 0
        line_length = 0
        for ttype, length in token_line:
            if line_pos >= xoffset:
                l = length
            elif line_pos+length >= xoffset:
                l = line_pos+length-xoffset
            else:
                l = 0

            if l:
                if line_pos+l > xoffset+num_chars:
                    l = xoffset+num_chars - line_pos
                if l: # is this nessary?
                    yield (ttype, l)

            line_length += l
            line_pos += length

        if line_length < num_chars+1:
            num_whitespace = num_chars+1-line_length
            yield (Token.Text.Whitespace, num_whitespace)

def make_pango_layout(view, widget=None):
    doc = view.document
    yoffset, xoffset = map(int, view.scroll_pos)
    chars, rows = map(int, view.textbox_dimensions)
    colours = view.colours
    tab_size = doc.tab_size

    if not widget:
        widget = view.textarea.drawingarea

    # only tokens for the text that's on the screen
    tokens = doc.tokenizer.get_normalised_tokens(yoffset, yoffset+rows)

    # pango layout
    #doc_lines = doc.get_lines(yoffset, yoffset+rows)
    start_index = doc.line_offsets[yoffset]
    if yoffset+rows < doc.num_lines:
        end_index = doc.line_offsets[yoffset+rows]
    else:
        end_index = len(doc.content)
    
    doc_lines = doc.content[start_index:end_index].splitlines()
    
    lines = []
    for line in doc_lines:
        line = line.replace('\t', ' '*doc.tab_size)
        lines.append(pad(line[xoffset:xoffset+chars], chars, tab_size))
    pl = widget.create_pango_layout("\n".join(lines))

    # build the list of pango attributes
    attrs = pango.AttrList()
    start_index = 0
    ltokens = line_tokens(tokens, tab_size)
    for ttype, length in clipped_tokens(ltokens, xoffset, chars):
        if not ttype is Token.Text.Whitespace:
            style = get_style_for_ttype(ttype)

            fg = colours[style]['pango']
            fg_attr = pango.AttrForeground(red=fg.red,
               green=fg.green,
               blue=fg.blue,
               start_index=start_index,
               end_index=start_index+length)
            attrs.insert(fg_attr)

            if colours[style].get('bold', False):
                wt_attr = pango.AttrWeight(
                    pango.WEIGHT_BOLD,
                    start_index=start_index,
                    end_index=start_index+length)
                attrs.insert(wt_attr)

            if colours[style].get('italic', False):
                st_attr = pango.AttrStyle(
                    pango.STYLE_ITALIC,
                    start_index=start_index,
                    end_index=start_index+length)
                attrs.insert(st_attr)

        start_index += length


    pl.set_attributes(attrs)

    return pl

def add_selection_to_layout(pl, colours, doc, selection, offset, size):
    yoffset, xoffset = offset
    chars, rows = size
    selection = selection.get_normalised()
    
    sel_start = doc.offset_to_cursor_pos(selection.start)
    sel_end = doc.offset_to_cursor_pos(selection.end)
    
    #print selection.start, selection.end, sel_start, sel_end
    
    scr_start = offset
    lastline_num = min(yoffset+rows-1, doc.num_lines-1)
    scr_end = (lastline_num, chars)
    
    # we're going to add attributes to this
    attrs = pl.get_attributes()
    
    # if the selection starts before the last position displayed and
    # it ends after the first position displayed, then the selection is
    # on screen
    if not (min(scr_end, sel_start) == sel_start and \
       min(scr_start, sel_end) == scr_start):
        # short-circuit so that we don't set all the attrs for nothing
        return
        
    start = max(sel_start, scr_start)
    end = min(sel_end, scr_end)

    endline_num = end[0]

    # work out the character positions to actual screen positions
    # by converting characters to spaces
    sy, sx = start
    sline = doc.get_line(sy)
    sx = char_pos_to_tab_pos(sline, sx, doc.tab_size)
    ey, ex = end
    eline = doc.get_line(ey)
    ex = char_pos_to_tab_pos(eline, ex, doc.tab_size)

    # cap the positions so that it is only the bit that's on screen
    start_pos = (cap(sy-yoffset, 0, rows), cap(sx-xoffset, 0, chars))
    end_pos = (cap(ey-yoffset, 0, rows), cap(ex-xoffset, 0, chars))

    sy, sx = start_pos
    ey, ex = end_pos
    if endline_num != sel_end[0]:
        # if this isn't the last line of the selection, then the
        # selection has to go to the end of the screen
        ex = chars

    # convert the (y, x) coordinates to indexes into the layout text
    start_index = sy*(chars+1)+sx # 1 for line ending
    end_index = ey*(chars+1)+ex

    # add the selection attribute
    bg = colours['sel']['pango']
    attr = pango.AttrBackground(red=bg.red, green=bg.green, \
        blue=bg.blue, start_index=start_index, end_index=end_index)
    attrs.insert(attr)
    
    pl.set_attributes(attrs)

#def add_selection_to_layout(pl, colours, doc, selection, offset, size):
#    xoffset, yoffset = offset
#    chars, rows = size
#    selection = selection.get_normalised()
#
#    start = (xoffset, yoffset)
#    lastline_num = min(doc.num_lines-1, yoffset+rows-1)
#    end = (chars, lastline_num)
#
#    attrs = pl.get_attributes()
#
#    # if the selection starts before the last position displayed and
#    # it ends after the first position displayed, then the selection is
#    # on screen
#    if min_pos(selection.start, end) == selection.start and \
#    min_pos(selection.end, start) == start:
#        start_pos = max_pos(selection.start, start)
#        end_pos = min_pos(selection.end, end)
#
#        endline_num = end_pos[1]
#
#        # work out the character positions to actual screen positions
#        # by converting characters to spaces
#        sx, sy = start_pos
#        sline = doc.get_line(sy)
#        sx = char_pos_to_tab_pos(sline, sx, doc.tab_size)
#        ex, ey = end_pos
#        eline = doc.get_line(ey)
#        ex = char_pos_to_tab_pos(eline, ex, doc.tab_size)
#
#        # cap the positions so that it is only the bit that's on screen
#        start_pos = (cap(sx-xoffset, 0, chars), cap(sy-yoffset, 0, rows))
#        end_pos = (cap(ex-xoffset, 0, chars), cap(ey-yoffset, 0, rows))
#
#        sx, sy = start_pos
#        ex, ey = end_pos
#        if endline_num != selection.end[1]:
#            # if this isn't the last line of the selection, then the
#            # selection has to go to the end of the screen
#            ex = chars
#
#        # convert the (x, y) coordinates to indexes into the layout text
#        start_index = sy*(chars+1)+sx # 1 for line ending
#        end_index = ey*(chars+1)+ex
#
#        # add the selection attribute
#        bg = colours['sel']['pango']
#        attr = pango.AttrBackground(red=bg.red, green=bg.green, \
#            blue=bg.blue, start_index=start_index, end_index=end_index)
#        attrs.insert(attr)
#
#    pl.set_attributes(attrs)

