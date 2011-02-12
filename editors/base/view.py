import bisect
from hashlib import md5
from pygments.token import Token
from ni.actions.base import EditAction


# Basically a view wraps a document and remembers stuff like the scrolling
# position, the cursor position, the selection and so on. That's so that some
# editors can do stuff like have multiple views open on the same document.
# This is just an interface and actual editors should inherit from View.

# TODO: these should probably be pluggable per mode
OPEN_BRACKETS = {
    u'{': u'}',
    u'(': u')',
    u'[': u']',
}
CLOSE_BRACKETS = {
    u'}': u'{',
    u')': u'(',
    u']': u'[',
}

def find_bracket_in_token(tvalue, token_offset, cursor_offset):
    """
    Find the position of the bracket character in the multi-char punctuation
    token that's at the cursor position.
    """

    brackets = set(OPEN_BRACKETS.keys()+CLOSE_BRACKETS.keys())    
    for i, char in enumerate(tvalue):
        if token_offset+i == cursor_offset-1:
            if char in brackets:
                return char, i
    return None

def fake_punc_tokens(tokens, index, char_offset):
    """
    A generator that returns the tokens from pos onwards. It turns multi-
    character punctuation tokens into 'fake' one-char tokens and sets offset
    for the position inside that token. It skips the first offset chars of the
    first multi-char punctuation token or the first token, because that one was
    the one that matched (the opening bracket).
    """

    total_tokens = len(tokens)
    is_first = True

    while index < total_tokens:
        ttype, tvalue = tokens[index]
        if ttype is Token.Punctuation:
            for i, char in enumerate(tvalue):
                if not is_first or i > char_offset:
                    yield ttype, char, index, i

        else:
            if not is_first:
                yield ttype, tvalue, index, 0

        is_first = False
        index += 1


def fake_punc_tokens_reverse(tokens, index, char_offset):
    """
    Similar to fake_punc_tokens, but in reverse (for closing brackets)
    """

    is_first = True

    while index >= 0:
        ttype, tvalue = tokens[index]
        if ttype is Token.Punctuation:
            for i, char in reversed(list(enumerate(tvalue))):
                if not is_first or i < char_offset:
                    yield ttype, char, index, i

        else:
            if not is_first:
                yield ttype, tvalue, index, 0

        is_first = False
        index -= 1


class View(object):
    def __init__(self, editor, document):
        self.editor = editor
        self.document = document
        self.cursor_pos = (0, 0) # or should this change to offset?
        self.scroll_pos = (0, 0)
        self.last_x_pos = 0 # This is not the index into the line, but the
                            # position on screen after tabs are taken into
                            # account so that we can get the cursor as close
                            # to it as possible when we navigate around.
        self.selection = None

        self.previous_action = None

    def invalidate(self):
        raise NotImplemented

    def _get_textbox_dimensions(self):
        raise NotImplemented
    textbox_dimensions = property(_get_textbox_dimensions)

    def _get_page_size(self):
        raise NotImplemented
    page_size = property(_get_page_size)

    def calculate_brackets(self):
        """
        Set self.brackets to the (x, y) position of the matching bracket.

        (Actually self.brackets is a sequence of all the positions to hilight,
         but for now it is always zero length)
        """

        # clear brackets so that if we short-circuit later it is safe
        self.brackets = []

        cy, cx = self.cursor_pos

        if cx == 0:
            return # start of the line guaranteed not to match

        # cache some lookups
        cursor_pos = self.cursor_pos
        doc = self.document
        tokenizer = doc.tokenizer        
        tokens = tokenizer.tokens
        offsets = tokenizer.offsets

        def find_offset(offsets, offset):
            pos = bisect.bisect_left(offsets, offset)        
            if pos >= len(offsets):
                # bisect_left might return an index outside of the list 
                pos = len(offsets)-1
            elif offsets[pos] > offset:
                # if the offset of the line index bist_left returns is after the 
                # offset we're looking for, use the previous line 
                pos -= 1
            return pos
        
        # find the index in offsets that refers to the token that contains the
        # character under the cursor
        cursor_offset = doc.cursor_pos_to_offset(cursor_pos)
        index = find_offset(offsets, cursor_offset)
        # we look at the previous token to find the relevant bracket
        index -= 1
        ttype, tvalue = tokens[index]
        if not ttype is Token.Punctuation:
            return

        # sometimes the tokenizer will return adjacent punctuation tokens 
        # grouped into one, so we have to find the token inside that
        token_offset = offsets[index]
        r = find_bracket_in_token(tvalue, token_offset, cursor_offset)
        if not r:
            # shouldn't realistically happen, but you never know
            # what any of the many lexers out there will do..
            return
        bracket, char_offset = r

        if OPEN_BRACKETS.has_key(bracket):
            matching = OPEN_BRACKETS[bracket]

            # For now we lex to the end so that we know that everything
            # is there to be checked. 
            # TODO: This should be easy to optimise..
            doc.update_tokens(self.scroll_pos,
                              self.textbox_dimensions,
                              to_end=True)

            stack = 0
            for r in fake_punc_tokens(tokens, index, char_offset):
                ttype, tvalue, index, char_offset = r
                if ttype is Token.Punctuation:
                    if tvalue == bracket:
                        stack += 1
                    elif tvalue == matching:
                        if stack > 0:
                            stack -= 1
                        else:
                            token_offset = offsets[index]
                            if token_offset:
                                bracket_offset = token_offset+char_offset
                            self.brackets = (bracket_offset,)
                            return

        elif CLOSE_BRACKETS.has_key(bracket):
            matching = CLOSE_BRACKETS[bracket]

            stack = 0
            for r in fake_punc_tokens_reverse(tokens, index, char_offset):
                ttype, tvalue, index, char_offset = r
                if ttype is Token.Punctuation:
                    if tvalue == bracket:
                        stack += 1
                    elif tvalue == matching:
                        if stack > 0:
                            stack -= 1
                        else:
                            token_offset = offsets[index]
                            if token_offset:
                                bracket_offset = token_offset+char_offset
                            self.brackets = (bracket_offset,)
                            return

        else:
            return

    def check_cursor(self):
        """
        Make sure the cursor is on the screen and scroll if necessary.
        """

        doc = self.document

        maxcol, maxrow = self.textbox_dimensions
        y, x = self.cursor_pos
        topy, topx = self.scroll_pos

        # sanity checks
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if topx < 0:
            topx = 0
        if topy < 0:
            topy = 0

        if x < topx:
            topx = x
        if y < topy:
            topy = y
        if x >= (topx+maxcol-1):
            topx = x - maxcol + 2
        if y >= (topy+maxrow-1):
            topy = y - maxrow + 2
        
        # don't scroll too far:
        if topy > doc.num_lines-maxrow+2:
            topy = doc.num_lines-maxrow+2
        
        if topx < 0:
            topx = 0
        
        if topy < 0:
            topy = 0

        line = doc.get_line(y)
        if len(line) < maxcol:
            topx = 0

        self.cursor_pos = y, x
        self.scroll_pos = topy, topx

    def execute_action(self, action):
        """
        Common code for executing an action. Actual editors will almost
        certainly do stuff before and after calling this.
        """

        # group similar actions so that we can undo/redo them together
        # TODO: is hash() safe in this context?
        if isinstance(action, type(self.previous_action)):
            if self.previous_action.grouped:
                action.grouped = hash(self.previous_action.grouped)
            else:
                self.previous_action.grouped = hash(self.previous_action)
                action.grouped = hash(self.previous_action)

        action.execute()
        if isinstance(action, EditAction):
            self.document.undo_stack.push(action)
            self.document.redo_stack.clear()

        self.previous_action = action
        
        self.check_cursor()
