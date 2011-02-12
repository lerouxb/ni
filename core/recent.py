import re


RECENT_RE = re.compile("(?P<filename>.*)\ (\((?P<sy>\d+), (?P<sx>\d+)\)) (\((?P<cy>\d+), (?P<cx>\d+)\))")

class RecentFileFormatError(Exception):
    pass

def parse_recent_line(line):
    """
    Return (filename, scroll_pos, cursor_pos) or raise RecentFileFormatError.

    Will make sure filename is unicode.
    """

    if not isinstance(line, unicode):
        # not so sure that this is the best way to do this..
        try:
            # assume the file is in utf8
            line = line.decode('utf8')
        except UnicodeDecodeError:
            raise RecentFileFormatError(line)

    line = line.rstrip('\n')
    match = RECENT_RE.match(line)
    if match:
        d = match.groupdict()
        
        scroll_pos = (int(d['sy']), int(d['sx']))
        cursor_pos = (int(d['cy']), int(d['cx']))
        return d['filename'], scroll_pos, cursor_pos
    else:
        raise RecentFileFormatError(line)

def format_recent_line(location, scroll_pos, cursor_pos):
    """
    Return a string in the correct format to represent a file so that we can
    restore it again later. Will always be unicode.
    """

    scroll_pos = u"%s" % (tuple(map(int, scroll_pos)),)
    cursor_pos = u"%s" % (tuple(map(int, cursor_pos)),)
    line = u"%s %s %s" % (location, scroll_pos, cursor_pos)
    return line

def get_recent_files_from_lines(lines):
    """
    Yield the recent file info stored in lines. Ignores errors.
    """

    for line in lines:
        try:
            yield parse_recent_line(line)
        except RecentFileFormatError:
            pass

def get_recent_files(filename):
    """
    Yield the recent file info stored in filename.
    """

    fle = open(filename)
    try:
        for line in get_recent_files_from_lines(fle):
            yield line
    finally:
        fle.close()
