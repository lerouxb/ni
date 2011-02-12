import gtk
from ni.core.benchmark import BenchmarkTimer, format_report
from ni.core.document import Document, load_document
from ni.editors.base.settings import BaseSettings
from ni.editors.base.editor import Editor
from ni.editors.base.view import View
from ni.editors.gtk.utils import make_pango_layout, get_gtk_colours
from ni.editors.gtk.settings import load_gtk_settings


class FakeEditor(Editor):
    def __init__(self):
        super(FakeEditor, self).__init__()
        self.settings = BaseSettings("/tmp/settings/test_settings")
        self.dimensions = (80, 24)

    def new_view(self, location=None):
        if location:
            document = load_document(location, self.settings)
        else:
            s = self.settings
            document = Document(encoding=s.encoding,
                                linesep=s.linesep,
                                tab_size=s.tab_size,
                                title="Untitled")
        view = FakeView(self, document)
        self.views.append(view)
        return view

    #def copy_view(self):
    #    """Make a copy of the view and return it."""
    #    raise NotImplementedError()

    #def close_view(self, view):
    #    """Close the specified view."""
    #    raise NotImplementedError()

    #def switch_current_view(self, view):
    #    """Switch the active document to the one specified."""
    #    raise NotImplementedError()

class FakeView(View):
    def __init__(self, editor, document):
        super(FakeView, self).__init__(editor, document)
        self.colours = None # set this later

    def _get_textbox_dimensions(self):
        return self.editor.dimensions
    textbox_dimensions = property(_get_textbox_dimensions)

    def _get_page_size(self):
        width, height = self.editor.dimensions
        return width-1, height-1
    page_size = property(_get_page_size)


def get_colours(widget, lexer, colourscheme):
    if lexer:
        mode = lexer.name
    else:
        mode = 'plain'
    return get_gtk_colours(widget, colourscheme, mode)


if __name__ == "__main__":
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    filename = '/home/leroux/projects/ni/benchmarks/make_pango_layout.py'
    editor = FakeEditor()
    #editor.dimensions = (100, 50)
    view = editor.new_view(filename)

    # just use the first colourscheme
    settings = load_gtk_settings()
    colourschemes = settings.load_colourschemes()
    colourscheme = colourschemes[0]

    # make a widget and show it so that we have a widget to use to allocate
    # colours and pass it to make_pango_layout (which uses it to make a new
    # layout)
    widget = gtk.Window()
    widget.show()

    view.colours = get_colours(widget,
                               view.document.tokenizer.lexer,
                               colourscheme)

    offset = (0, 0)
    size = view.textbox_dimensions
    tab_size = 8

    b = BenchmarkTimer()

    for x in xrange(1000):
        b.start("Warmup (must relex)")
        view.document.invalidate((0, 0))
        view.document.update_tokens(offset, size)
        layout = make_pango_layout(view, widget)
        b.end()

    for x in xrange(1000):
        b.start("Normal (no lexing)")
        view.document.update_tokens(offset, size)
        layout = make_pango_layout(view, widget)
        b.end()

    print

    report = b.get_report()
    print format_report(report)

