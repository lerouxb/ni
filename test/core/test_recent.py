import os
import unittest
import tempfile
from nose.tools import *
from ni.core.recent import RecentFileFormatError, parse_recent_line, \
    format_recent_line, get_recent_files_from_lines, get_recent_files


VALID_LINE = u"/home/leroux/test.py (0, 0) (12, 4)"

ERROR_LINE = u"/home/leroux/test.py"

LINES = u"""
/home/leroux/projects/ni/ni_gtk.py (0, 0) (21, 29)
/home/leroux/projects/ni/ni_urwid.py (0, 0) (20, 8)
/home/leroux/projects/ni/editors/gtk/dialogs.py (0, 0) (15, 43)
this one is invalid and should be silently ignored
/home/leroux/projects/ni/editors/gtk/menu.py (163, 163) (0, 0)
/home/leroux/projects/ni/editors/gtk/search.py (0, 0) (0, 0)
/home/leroux/Desktop/tree.py (29, 0) (30, 0)
""".strip().encode('utf8').split('\n')

def test_parse_recent_line():
    filename, scroll_pos, cursor_pos = parse_recent_line(VALID_LINE)
    assert filename == '/home/leroux/test.py'
    assert scroll_pos == (0, 0)
    assert cursor_pos == (4, 12)

@raises(RecentFileFormatError)
def test_parse_recent_line_fail():
    filename, scroll_pos, cursor_pos = parse_recent_line(ERROR_LINE)

def test_format_recent_line():
    location = '/home/leroux/test.py'
    scroll_pos = (0, 0)
    cursor_pos = (4, 12)

    line = format_recent_line(location, scroll_pos, cursor_pos)
    assert line == VALID_LINE

def test_get_recent_files_from_lines():
    filenames = []
    for r in get_recent_files_from_lines(LINES):
        filename, scroll_pos, cursor_pos = r
        filenames.append(filename)

    assert len(filenames) == len(LINES)-1 # there should be one error

def test_get_recent_files():
    handle, name = tempfile.mkstemp(text=True)
    try:
        fle = open(name, 'w')
        fle.write('\n'.join(LINES))
        fle.close()

        filenames = []
        for r in get_recent_files(name):
            filename, scroll_pos, cursor_pos = r
            filenames.append(filename)

        assert len(filenames) == len(LINES)-1 # there should be one error

    finally:
        os.unlink(name)
