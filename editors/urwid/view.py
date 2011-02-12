from ni.editors.base.view import View


class UrwidView(View):
    def __init__(self, editor, document):
        super(UrwidView, self).__init__(self, document)
        self.is_valid = False
        self.editor = editor

    def _get_textbox_dimensions(self):
        return self.editor.textbox_dimensions
    textbox_dimensions = property(_get_textbox_dimensions)

    def _get_page_size(self):
        return self.editor.textbox_dimensions
    page_size = property(_get_page_size)

    def invalidate(self):
        self.is_valid = False # this gets checked later

    def execute_action(self, action):
        super(UrwidView, self).execute_action(action)

        self.editor.check_cursor()

        if not self.is_valid:
            self.is_valid = True
            self.editor.redraw_all = True
            #self.editor.draw()
