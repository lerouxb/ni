class Selection(object):
    def __init__(self, document, start, end):
        self.document = document
        self.start = start
        self.end = end
    
    def __unicode__(self):        
        return u"%s to %s" % (self.start, self.end)
    
    def get_normalised(self):
        if self.start > self.end:
            return Selection(self.document, self.end, self.start)
        return self
    
    def get_content(self):
        selection = self.get_normalised()
        return self.document.content[selection.start:selection.end+1]
    
    def line_in_selection(self, y, normalised=False):
        if normalised:
            selection = self
        else:
            selection = self.get_normalised()
        
        sy, sx = self.document.offset_to_cursor_pos(self.start)
        ey, ex = self.document.offset_to_cursor_pos(self.end)
        
        if y >= sy and y <= ey:
            return True
        
        return False
    
    def in_selection(self, offset, normalised=False):
        if normalised:
            selection = self
        else:
            selection = self.get_normalised()
        
        if offset >= selection.start and offset <= selection.end:
            return True
        
        return False

