import re


WORD_RE = re.compile('[\w]+')
WHITESPACE_RE = re.compile('[\s]+')
SYMBOL_RE = re.compile('[^\w\s]+')

def normalise_line_endings(text, linesep='\n'):
    newtext = '\n'.join(text.splitlines())
    if text.endswith('\r') or text.endswith('\n'):
        newtext += '\n'
    return newtext

def get_line_length(text, start, linesep='\n'):
    # work out where the line ends so that we don't place the cursor past
    # the end of the line
    max_offset = text.find(linesep, start)
    if max_offset == -1:
        # we're on the last line, so the last character in the file
        max_offset = len(text)
    return max_offset

def tab_len(s, tab_size):
    """
    Get the "virtual" character length of a string where each tab character
    takes tab_size characters.
    """

    ntabs = s.count('\t')
    return len(s) - ntabs + ntabs*tab_size

def char_pos_to_tab_pos(s, x, tab_size):
    """
    Get the "virtual" character position for the specified character where each
    tab character takes tab_size characters.
    """

    return tab_len(s[:x], tab_size)

def tab_pos_to_char_pos(s, x, tab_size):
    """
    Return the nearest index into the string (s) that corresponds with the
    "cursor position" (x) specified. If because of tabs it cannot map it
    directly to an index, it will return the closest index smaller than the
    cursor position.

    Cursor position here corresponds to the column on screen where the cursor
    appears, when tabs are taken into account. (starting at 0) Logical position
    perhaps?

    For example. for the string "\tHello" with tab_size == 8 and x == 5, it
    will return 0. With x == 8 it will return 1. With x == 9 it will
    return 2.
    """

    last_pos = 0
    pos = 0
    for char in s:
        if char == '\t':
            pos += 8
        else:
            pos += 1
        if pos > x:
            return last_pos
        elif pos == x:
            return pos
        last_pos = pos

    return last_pos

def pad(line, maxcol, tab_size=8):
    """
    Pads a string with spaces so that the "virtual" length is maxcol long.
    """

    if len(line) < maxcol:
        chars_needed = maxcol-tab_len(line, tab_size)
        line += ' ' * chars_needed
    return line

def get_word_range(line, x):
    """
    Return the start and end positions of the word around the given position
    in the line.
    """

    if not len(line):
        return None

    if x == len(line):
        char = line[x-1]
    else:
        char = line[x]

    if WORD_RE.match(char):
        rexp = WORD_RE
    elif WHITESPACE_RE.match(char):
        rexp = WHITESPACE_RE
    else:
        rexp = SYMBOL_RE

    span = None
    for match in rexp.finditer(line):
        start, end = match.span()
        if x >= start and x <= end:
            span = start, end
            break

    return span

def cap(value, minimum, maximum):
    """
    Make sure value is >= minimum and <= maximum and adjust accordingly.
    """

    if value < minimum:
        return minimum
    elif value > maximum:
        return maximum
    else:
        return value

def slugify(value): # lifted from django
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """

    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

