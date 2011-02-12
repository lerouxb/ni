#!/usr/bin/env python

import sys
import os
import urwid

try:
    from ni.editors.urwid.editor import UrwidEditor
except ImportError:
    sys.path.append(os.path.join(os.path.expanduser(os.path.curdir), '..'))
    from ni.editors.urwid.editor import UrwidEditor


def main():
    from optparse import OptionParser
    parser = OptionParser(usage='%prog [options] <filename>*')
    options, args = parser.parse_args(sys.argv[1:])

    try:
        ui = urwid.raw_display.Screen()
        editor = UrwidEditor(ui)

        for filename in args:
            if filename[0] == os.path.sep:
                path = filename
            else:
                path = os.path.join(os.path.realpath(os.path.curdir), filename)
            if os.path.exists(path) and os.path.isfile(path):
                editor.new_view(path)

        ui.run_wrapper(editor.run)

    except IndexError:
        # try and debug weird intermittent error
        print editor.view.cursor_pos
        print editor.view.scroll_pos
        #print editor.view.document.tokenizer.from_line
        #print editor.view.document.tokenizer.to_line

    finally:
        pass


if __name__ == "__main__":
    main()
