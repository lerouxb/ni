import os
import bisect
from pygments.token import Token
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, \
    ClassNotFound


# TODO: these really have to be moved to another file and it should be made
# to be pluggable

def isbacktracetoken_default(ttype, tvalue):
    return not ttype in Token.Literal

def isbackspacetoken_html(ttype, tvalue):
    if not tvalue:
        return False

    if ttype in Token.Name.Tag:
        if tvalue == '>' or tvalue[0] == '<' and rvalue[-1] == '>':
            return True

    return False

def isbacktracetoken_css(ttype, tvalue):
    return ttype in Token.Punctuation and tvalue == '}'

class Tokenizer(object):
    """
    Wraps a lexer and caches tokens and token offsets.
    """
    
    def __init__(self, document):        
        self.document = document
        self.tokens = []
        self.offsets = []        
        self.end = 0 # up to where we lexed last
        
        if document.location:
            filename = document.location
            try:
                # HACK! overrides should come from settings...
                if os.path.splitext(filename)[1] == '.html':
                    # assume django template
                    self.lexer = get_lexer_by_name('html+django',
                                                   stripnl=False,
                                                   encoding='utf8')
                elif os.path.splitext(filename)[1] == '.py':
                    # otherwise we end up with the annoying NumPy lexer..
                    self.lexer = get_lexer_by_name('python',
                                                   stripnl=False,
                                                   encoding='utf8')
                else:
                    self.lexer = get_lexer_for_filename(filename,
                                                        stripnl=False,
                                                        encoding='utf8')
            except ClassNotFound:
                self.lexer = None
        else:
            self.lexer = None
    
    def update(self, from_offset=None, to_offset=None):
        """
        Update the tokens and offsets from from_offset to to_offset.
        
        This should only ever get used from inside Document.
        """
        
        content = self.document.content
        
        if not self.lexer:
            self.tokens = [(Token.Text, content)]
            self.offsets = [0]
            return
        
        # default to_offset to the end of the content
        if not to_offset:
            to_offset = len(content)
        
        if not self.tokens:
            # if we haven't lexed before, make sure we take the long path
            from_offset = None

        if from_offset == None:
            # lex everything
            from_offset = 0
            self.end = 0
            self.tokens = []
            self.offsets = []
            
            code = content
        
        else:
            # make sure from_offset is actually inside the bit that we already
            # have cached
            if self.offsets:
                last_offset = self.offsets[-1]
            else:
                last_offset = 0
            from_offset = min(last_offset, from_offset)
            
            # HACK!
            # Try and "snap" to a token (previous non-literal token, at least
            # two back)
            if self.lexer.name in ('HTML', 'HTML+Django/Jinja'):
                isbacktracetoken = isbacktracetoken_html
            elif self.lexer.name == 'CSS':
                isbacktracetoken = isbacktracetoken_css
            else:
                isbacktracetoken = isbacktracetoken_default
            
            index = bisect.bisect_left(self.offsets, from_offset)
            index -= 2
            if index < 0:
                index = 0
            else:
                while index:
                    tokentype, value = self.tokens[index]
                    if isbacktracetoken(tokentype, value):
                        break
                    index -= 1
            
            # set self.end, self.tokens and self.offsets (frop the bits from 
            # the cache that we are replacing, basically)
            from_offset = self.offsets[index]
            self.end = self.offsets[index]
            self.tokens = self.tokens[:index]
            self.offsets = self.offsets[:index]
            
            # sanity
            if to_offset < from_offset:
                to_offset = from_offset
            
            # cut the visible portion
            code = content[from_offset:to_offset+1]
        
        # lex the code fragment and add the tokens and their corresponding
        # starting offsets (while caching the end position)
        
        for tokentype, value in self.lexer.get_tokens(code):
            # hack for python
            if tokentype is Token.Name.Builtin.Pseudo and value == 'self':
                tokentype = Token.Name.Builtin.Pseudo.Self

            self.tokens.append((tokentype, value))
            self.offsets.append(self.end)

            self.end += len(value.replace('\t', ' '*self.document.tab_size))

    def get_normalised_tokens(self, from_line, to_line):
        """
        Return tokens for the region extending from from_line to to_line and
        the first and last tokens chopped if they extend out of the specified
        section.
        
        It typically gets used in drawing routines and should only be called
        after update(), because it doesn't update the tokens itself - it just
        reads from the cached tokens and offsets.
        """
        
        tokens = self.tokens
        offsets = self.offsets
        
        sy = from_line
        start_offset = self.document.cursor_pos_to_offset((sy, 0))
        
        ey = to_line+1
        end_offset = self.document.cursor_pos_to_offset((ey, 0))
        if self.document.offset_to_cursor_pos(end_offset)[0] == ey:
            # it didn't get adjusted, so we're not at the end of the file, 
            # therefore we should go to the start of the previous line
            end_offset -= 1
        
        # get the token index that contains the start offset
        start_index = bisect.bisect_left(offsets, start_offset)
        if start_index and \
        start_index >= len(offsets) or offsets[start_index] > start_offset:
            start_index -= 1
        
        # get the token index that contains the end offset
        end_index = bisect.bisect_left(offsets, end_offset)        
        if end_index and \
        end_index >= len(offsets) or offsets[end_index] > end_offset:
            end_index -= 1
        
        # chop the tokens to only include the ones we're interested in
        ntokens = tokens[start_index:end_index+1]
        
        # chop the first token if it extends out of the screen        
        if offsets[start_index] < start_offset:
            start_skip = start_offset - offsets[start_index]
            ttype, tvalue = ntokens[0]
            ntokens[0] = (ttype, tvalue[start_skip:])
        
        # chop the last token if it extens out of the screen
        if offsets[end_index] > end_offset:
            end_skip = offsets[end_index] - end_offset                
            ttype, tvalue = ntokens[-1]
            ntokens[-1] = (ttype, tvalue[:-end_skip])
        
        # NOTE: I'm pretty sure there's an edge case here involving very long
        # tokens, but I can't recreate it right now..
        
        return ntokens
