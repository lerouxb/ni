from pygments.token import Token

def make_statusline(size, left="", center="", right="", leftstyle='statusbar' ,\
  centerstyle='statusbar', rightstyle='statusbar'):
    width = size[0]

    if center:
        side_space_available = width/2 - len(center)/2
        if len(left) > side_space_available:
            left = left[:side_space_available-3]+'..'

        if len(right) > side_space_available:
            right = right[:side_space_available-3]+'..'

        left_spaces = width/2-len(center)/2-len(left)
        right_spaces = width/2-len(center)/2-len(right)

        if len(left)+left_spaces+len(center)+right_spaces+len(right) > width:
            left_spaces -= 1

        markup = [(leftstyle, left), \
          (centerstyle, ' '*left_spaces+center+' '*right_spaces), \
          (rightstyle, right)]

    else:
        if len(left) > width or len(right) > width:
            return '' # don't even bother if they are both too long

        length = len(left)+len(right)
        if length > width:
            # if left and right together is longer than width, chop the
            # -longest- left one shorter
            ##if len(left) > len(right):
            ##    left = left[:width-len(right)]
            ##else:
            ##    right = left[:width-len(left)]
            left = '..'+left[-(width-4-len(right)):] # 4 == .. and two spaces
            spaces = 2
        else:
            spaces = width-length

        markup = [(leftstyle, left), (centerstyle, ' '*spaces), \
          (rightstyle, right)]

    return markup

def get_urwid_lines_attrs((columns, rows), (scrolly, scrollx), tokens, selection):
    """return lines, attrs"""

    def get_style(ttype):
        if ttype in Token.Text:
            return 'plain'
        #if ttype in Token.Selection:
        #    return 'selection'
        if ttype in Token.Error:
            return 'error'
        if ttype in Token.Other:
            return 'other'
        if ttype in Token.Keyword:
            return 'keyword'
        if ttype in Token.Name:
            return 'name'
        if ttype in Token.Literal:
            return 'literal'
        if ttype in Token.Operator:
            return 'operator'
        if ttype in Token.Punctuation:
            return 'punctuation'
        if ttype in Token.Comment:
            return 'comment'
        if ttype in Token.Generic:
            return 'generic'

    lines = []
    current_line = []

    for ttype, value in tokens:
        style = get_style(ttype)
        for char in value:
            if char == '\n':
                lines.append(current_line)
                current_line = []
            else:
                current_line.append((style, char))

    if current_line:
        lines.append(current_line)

    # make sure line length is columns max, starting from scrollx
    lines = [l[scrollx:][:columns] for l in lines]

    text_lines = []
    attrs = []

    if selection:
        selection = selection.get_normalised()

    y = scrolly
    for l in lines:
        x = scrollx
        current_style = None
        num_chars = 0
        line = ''
        line_attrs = []

        for style, char in l:
            line += char
            if selection and selection.in_selection((x, y), True):
                style = 'sel_'+style

            if style != current_style:
                if current_style:
                    line_attrs.append((current_style, num_chars))
                current_style = style
                num_chars = 1
            else:
                num_chars += 1

            x += 1

        if current_style:
            line_attrs.append((current_style, num_chars))

        # fill up the rest of the line to make sure it is 'columns' wide
        if len(l) < columns:
            if selection and \
             (len(l) == 0 and selection.in_selection((0, y), True) or \
             len(l) != 0 and selection.in_selection((len(l)+1, y), True)):
                style = 'sel_plain'
            else:
                style = 'plain'
            line += (columns-len(l))*' '
            line_attrs.append((style, columns-len(l)))

        text_lines.append(line)
        attrs.append(line_attrs)
        y += 1

    text_lines = text_lines[:rows]
    attrs = attrs[:rows]

    # fill in the rest of the screen with lines starting with -
    #for i in xrange(len(text_lines), rows):
    #    text_lines.append('-' + ' '*(columns-1))
    #    attrs.append([('empty', 1), ('plain', columns-1)])

    for i in xrange(len(text_lines), rows):
        text_lines.append(' '*(columns))
        attrs.append([('plain', columns)])

    return text_lines, attrs

