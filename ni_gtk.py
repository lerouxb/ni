#!/usr/bin/env python

import sys
import os
import gtk

try:
    from ni.editors.gtk.editor import GTKEditor
except ImportError:
    sys.path.append(os.path.join(os.path.expanduser(os.path.curdir), '..'))
    from ni.editors.gtk.editor import GTKEditor

from ni.editors.gtk.settings import GLADE_DIR, GLOBAL_COLOURSCHEMES_DIR

def main():
    from optparse import OptionParser

    parser = OptionParser(usage='%prog [options] <filename>*')
    options, args = parser.parse_args(sys.argv[1:])


    editor = GTKEditor()

    for filename in args:
        if filename[0] == os.path.sep:
            path = filename
        else:
            path = os.path.join(os.path.realpath(os.path.curdir), filename)
        if os.path.exists(path) and os.path.isfile(path):
            editor.new_view(path)

    gtk.main()

if __name__ == "__main__":
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    must_exit = False
    for path in (GLADE_DIR, GLOBAL_COLOURSCHEMES_DIR):
        if not os.path.exists(path):
            err = "ERROR: %s does not exist." % (path,)
            sys.stderr.write(err+"\n")
            must_exit = True
    if must_exit:
        sys.exit(1)

    main()