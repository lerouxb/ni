import os
import bisect
from hashlib import md5
from ni.core.tokenizer import Tokenizer
from ni.core.stack import Stack
from ni.core.text import get_line_length, normalise_line_endings
from ni.core.files import load_textfile
from ni.core.selection import Selection


def load_document(location, settings):
    textfile = load_textfile(location)

    kwargs = {
        'encoding': textfile['encoding'],
        'linesep': textfile['linesep'],
        'tab_size': settings.tab_size, # TODO: try and detect first
        'location': location,
        'content': textfile['content'],
    }

    return Document(**kwargs)

class Document(object):
    """
    Representation of a text file / buffer.
    
    ATTRIBUTES:

    location      -- Filepath. Can be None if title is filled in.
    title         -- Temporary title for when location is not filled in.
    encoding      -- For use with encode() and decode() for converting to and
                     from unicode strings.
    linesep       -- Line separator character(s).
    tab_size      -- Width of a tab in number of characters. (e.g. 2, 4, 8)
    line_offsets  -- offset for the first character of each line
    undo_stack    -- Stack that contains Action objects.
    redo_stack    -- Stack that contains Action objects.
    tokenizer     -- A Tokenizer instance.
    
    PROPERTIES:
    
    is_modified   -- Boolean value that states if the document has been
                     modified.
    must_relex    -- The document had changes made since the last time it got
                     lexed.
    description   -- Returns either the filename if it is set, otherwise it
                     will return the title.
    num_lines     -- return the number of lines.

    METHODS:
    
    offset_to_cursor_pos -- return (y, x) for the character
    cursor_pos_to_offset -- return closest offset
    get_line      -- Return a specific line
    insert        -- Insert text at the specified position.
    delete        -- Delete text between the specified positions.
    invalidate    -- Mark where a document must be retokenized/drawn
    save          -- Save the document to a file (specified by location)
    update_tokens -- Lex enough of the document to fill the view (or all of it
                     if to_end is set)

    NOTES: 
    
    insert and delete shouldn't be used directly, but via InsertDelta and 
    DeleteDelta objects inside actions only. This ensures that all changes can 
    be undone or redone. (see actions/defaultactions.py)
    Action instances get added to undo_stack and these use Delta objects to 
    actually interact with the document.

    To load a document, use the load_document helper function.

    """

    def __init__(self, encoding='utf8', linesep='\n', tab_size=8,
                 location=None, title=None, content=None):
        if not (location or title):
            raise Exception("location or title is required")

        if location and title:
            raise Exception("location or title is required")

        # location of saved document or title for unsaved document
        self.location = location
        self.title = title

        # metadata
        self.encoding = encoding
        self.linesep = linesep
        self.tab_size = tab_size
        self.line_offsets = [0]
                
        # content
        content = content or u''
        if content and not isinstance(content, unicode):
            content = content.decode(encoding, 'ignore')        
        self._content = normalise_line_endings(content)

        self._adjust_line_offsets(0)

        # undo / redo action stacks (hardcoded sizes for now
        self.undo_stack = Stack(10000)
        self.redo_stack = Stack(10000)

        # Holds stuff like number of chars and md5 hash which we can check to 
        # see if the file is modified. This should be updated every time we 
        # save the file.
        self._modified_info = None

        # things invalidated by actions since the last redraw
        self._relex_from = None

        if self.location:
            self.tokenizer = Tokenizer(self)
        else:
            self.tokenizer = Tokenizer(self)

        if location:
            self._update_modified_info()
            # reset tokenizer
            self.tokenizer = Tokenizer(self)
            self.tokenizer.update()

    def _get_content(self):
        """
        Make sure you can't set content from the outside.
        """        
        return self._content
    content = property(_get_content)

    def _get_is_modified(self):
        """
        Efficiently check to see if the document has been modified.

        Uses self._modified_info to check if a document has been 
        modified since self._modified_info was last set.
        """

        if not self._modified_info:
            # this is a new file, so if there are any lines, then the
            # file was changed.
            if self.content:
                return True
            else:
                return False
        
        # if the content is not of the same length, 
        # then it must be modified
        if self._modified_info['num_chars'] != len(self.content):
            return True
        
        m = md5(self.content)
        return self._modified_info['md5_hexdigest'] != m.hexdigest()
    is_modified = property(_get_is_modified)

    def _get_must_relex(self):
        return self._relex_from != None
    must_relex = property(_get_must_relex)

    def _get_description(self):
        """
        Return filename or something descriptive if location is not set.
        """

        if self.location:
            path = os.path.dirname(self.location)
            home = os.path.expanduser('~')
            if path[:len(home)] == home:
                path = '~' + path[len(home):]
            filename = os.path.basename(self.location)
            return os.path.join(path, filename)

        else:
            return self.title
    description = property(_get_description)

    def _get_num_lines(self):
        return len(self.line_offsets)
    num_lines = property(_get_num_lines)

    def _update_modified_info(self):
        """
        Set self._modified_info.
        Should only be set initially and when we save.
        """

        info = {}

        info['num_chars'] = len(self.content)
        m = md5(self.content)
        info['md5_hexdigest'] = m.hexdigest()

        self._modified_info = info
    
    def offset_to_cursor_pos(self, offset):
        # check bounds
        if offset < 0:
            offset = 0
        offset = min(offset, len(self.content))
        
        # get the closest line (on or before the offset)
        y = bisect.bisect_left(self.line_offsets, offset)
        
        if y >= self.num_lines:
            # bisect_left might return an index outside of the list 
            y = self.num_lines-1
        elif self.line_offsets[y] > offset:
            # if the offset of the line index bist_left returns is after the 
            # offset we're looking for, use the previous line 
            y -= 1
        
        return (y, offset-self.line_offsets[y])

    def cursor_pos_to_offset(self, cursor_pos):
        y, x = cursor_pos

        # check bounds
        if y < 0:
            return 0        
        if y >= self.num_lines:
            return len(self.content)
        
        # don't put the cursor after the end of the line
        offset = self.line_offsets[y]
        max_offset = get_line_length(self.content, offset)
        return min(offset+x, max_offset)        

    def _adjust_line_offsets(self, offset):
        # TODO: this can be sped up a lot
        soffset = 0
        self.line_offsets = [0]
        
        while True:
            loffset = self.content.find('\n', soffset)
            if loffset == -1:
                break
            self.line_offsets.append(loffset+1)
            soffset = loffset+1

    def get_line(self, y):
        start_offset = self.line_offsets[y]
        if y+1 < self.num_lines:
            end_offset = self.line_offsets[y+1]-1
        else:
            end_offset = len(self.content)
        return self.content[start_offset:end_offset]

    def insert(self, offset, text):
        """
        Insert text at offset; update line_offsets.
        
        This should be used via InsertDelta so that we can undo it again.
        """

        self._content = self._content[:offset]+text+self._content[offset:]        
        self._adjust_line_offsets(offset)
    
    def delete(self, offset, length):
        """
        Delete length characters from offset; update line_offsets.
        
        This should be used via DeleteDelta so that we can undo it again.
        """

        self._content = self._content[:offset]+self._content[offset+length:]
        self._adjust_line_offsets(offset)
    
    def invalidate(self, offset):
        """
        Mark offset where the document must be retokenised / drawn.
        """
        
        if offset != None:
            if self._relex_from:
                self._relex_from = min(self._relex_from, offset)
            else:
                self._relex_from = offset

    def update_tokens(self, scroll_pos, size, to_end=False):
        """
        (re)lex part of the document if we need to 
        """
        
        if self.tokenizer.tokens:
            last_offset = self.tokenizer.offsets[-1]
            last_token = self.tokenizer.tokens[-1]
            last_offset += len(last_token[1].replace('\t', ' '*self.tab_size))
        else:
            last_offset = 0
        
        if to_end:
            # force to end
            last_needed_offset = len(self.content)
        else:
            # last needed is the end of the screen
            y, x = scroll_pos
            width, height = size
            lx = x + width - 1
            ly = y + height - 1
            last_needed_offset = self.cursor_pos_to_offset((ly+1, 0))
            if last_needed_offset:
                last_needed_offset -= 1
        
        must_update = False
        if self.must_relex:
            must_update = True
        elif not self.tokenizer.tokens:
            must_update = True
        elif min(last_offset, last_needed_offset) == last_offset:
            must_update = True
         
        if not must_update:
            return
        
        #print "updating"
        
        if self._relex_from == None:
            if not self.tokenizer.tokens:
                from_offset = 0
            else:
                from_offset = last_offset
        else:
            from_offset = self._relex_from
            self._relex_from = None
        
        #print "="*80
        #print from_offset, last_needed_offset
        
        self.tokenizer.update(from_offset, 
                              last_needed_offset)

    def save(self, location=None):
        """
        Save the document to self.location, update self._modified_info
        """

        old_location = self.location

        try:
            if location:
                self.location = location
                self.title = None
            
            if not self.location:
                raise Exception("Location not set.")
            
            content = self.content
            
            # if the document's linesep setting is not \n, 
            # then convert line endings
            if self.linesep != '\n':
                content = content.replace('\n', self.linesep)
            
            # TODO: I might have to write the file in binary mode or python
            # will just replace line endings anyway.
            f = open(self.location, "w")
            f.write(content.encode(self.encoding))
            f.close()

            self._update_modified_info()

            # reset tokenizer
            self.tokenizer = Tokenizer(self)
            self.tokenizer.update()
        
        except:
            self.location = old_location
            raise

class InsertDelta(object):
    def __init__(self, document, offset, text):
        self.document = document
        self.offset = offset
        if not isinstance(text, unicode):
            text = text.decode(self.document.encoding, 'ignore')
        self.text = normalise_line_endings(text)

    def do(self):
        doc = self.document
        doc.insert(self.offset, self.text)
        doc.invalidate(self.offset)

    def undo(self):
        doc = self.document
        doc.delete(self.offset, len(self.text))
        doc.invalidate(self.offset)

class DeleteDelta(object):
    def __init__(self, document, offset, length):
        self.document = document
        self.offset = offset
        self.length = length
        
        # Assume offset 0 and length 1: 
        # 0 to 0 is one character: the first one. so the selection shouldn't
        # be from 0 to 1
        s = Selection(document, offset, offset+length-1)
        self.deleted_content = s.get_content()
        #print "deleted: "+str(offset)+" |"+self.deleted_content+'|'

    def do(self):
        doc = self.document
        doc.delete(self.offset, self.length)
        doc.invalidate(self.offset)

    def undo(self):
        doc = self.document
        doc.insert(self.offset, self.deleted_content)
        doc.invalidate(self.offset)


