def curry(_curried_func, *args, **kwargs):
    def _curried(*moreargs, **morekwargs):
        return _curried_func(*(args+moreargs), **dict(kwargs, **morekwargs))
    return _curried


class MockView(object):
    def __init__(self, editor, document):
        self.editor = editor
        self.document = document
        self.is_valid = True     # so we can see if invalidate was called
        self.selection = None    # None or a Selection object
        self.cursor_pos = (0, 0)
        self.last_x_pos = 0
        self.scroll_pos = (0, 0)

    def invalidate(self):
        self.is_valid = False   # just set a flag so we can check it later

class InterfaceLoggingMock(object):
    def __init__(self):
        self.methods = {}

    def __getattr__(self, attr):
        return curry(self.flag_method, attr)

    def flag_method(self, name, *args, **kwargs):
        self.methods[name] = (args, kwargs)

