import unittest
from nose.tools import *
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from ni.editors.base.view import find_bracket_in_token, fake_punc_tokens, \
    fake_punc_tokens_reverse, View


#def test_find_bracket_in_token():
#    token_pos = (0, 0)
#    cursor_pos = (0, 0)
#
#    # at the start of the line, the cursor can't be "next" to a bracket
#    # (you have to be to the right of a bracket in order to be "next" to it)
#    assert find_bracket_in_token("{", token_pos, cursor_pos) == None
#
#    # the cursor is next to the {
#    token_pos = (0, 0)
#    cursor_pos = (1, 0)
#    assert find_bracket_in_token("{", token_pos, cursor_pos) == ('{', 0)
#
#    # multi-char token: the cursor is next to the (
#    token_pos = (0, 0)
#    cursor_pos = (2, 0)
#    assert find_bracket_in_token("{(", token_pos, cursor_pos) == ('(', 1)
#
#    # the token and the cursor aren't even on the same line
#    token_pos = (0, 0)
#    cursor_pos = (1, 1)
#    assert find_bracket_in_token("{", token_pos, cursor_pos) == None

TEST_CODE = u"""
var settings = jQuery.extend({
    animate: true
}, options);
""".strip()

#class TestPuncTokens(unittest.TestCase):
#    def setUp(self):
#        # all of this so we can have lists of tokens and positions
#
#        tab_size = 0
#
#        lexer = get_lexer_by_name('javascript',
#                                  stripnl=False,
#                                  encoding='utf8')
#
#        self.tokens = []
#        self.positions = []
#
#        end = (0, 0)
#        for ttype, tvalue in lexer.get_tokens(TEST_CODE):
#            self.tokens.append((ttype, tvalue))
#            self.positions.append(end)
#
#            # calculate the end position
#            x, y = end
#            fragments = tvalue.split("\n")
#            num_fragments = len(fragments)
#            if num_fragments > 1:
#                y += (num_fragments-1)
#                x = 0
#            x += len(fragments[-1].replace('\t', ' '*tab_size))
#
#            end = (x, y)
#
#    def test_fake_punc_tokens_sanity(self):
#        num_multichar_punc = 0
#        for ttype, tvalue in self.tokens:
#            if ttype is Token.Punctuation:
#                if len(tvalue) > 1:
#                    num_multichar_punc += 1
#        assert num_multichar_punc > 0 # should be 2
#
#        text = ''
#        punc_tokens = fake_punc_tokens(self.tokens, self.positions, 0, 0)
#        num_multichar_punc = 0
#        for ttype, tvalue, pos, offset in punc_tokens:
#            text += tvalue
#            if ttype is Token.Punctuation and len(tvalue) > 1:
#                num_multichar_punc += 1
#        assert num_multichar_punc == 0
#
#        # the first token should have been skipped
#        expected = ''.join([v for t, v in self.tokens[1:]])
#
#        assert text == expected
#
#    def test_fake_punc_tokens_find(self):
#        # get the position of the first multi-char token
#        position = None
#        i = 0
#        for ttype, tvalue in self.tokens:
#            if ttype is Token.Punctuation:
#                if len(tvalue) > 1:
#                    if position == None:
#                        position = i
#            i += 1
#        assert position != None # make sure pygments didn't change completely
#
#        x, y = self.positions[position]
#        x = x + 1
#        assert (x, y) == (29, 0) # { on first line
#
#        # start at the second bracket in the token at 'position'
#        punc_tokens = fake_punc_tokens(self.tokens,
#                                       self.positions,
#                                       position,
#                                       1)
#        found = False
#        for ttype, tvalue, pos, offset in punc_tokens:
#            if ttype is Token.Punctuation and tvalue == '}':
#                # look for a token that matches the closing bracket
#                found = True
#                break
#        assert found == True
#
#        x, y = self.positions[pos]
#        x = x + offset
#        assert (x, y) == (0, 2) # } on last line
#
#    def test_fake_punc_tokens_reverse_sanity(self):
#        punc_tokens = fake_punc_tokens_reverse(self.tokens,
#                                               self.positions,
#                                               len(self.positions)-1, 0)
#        num_multichar_punc = 0
#        for ttype, tvalue, pos, offset in punc_tokens:
#            if ttype is Token.Punctuation and len(tvalue) > 1:
#                num_multichar_punc += 1
#        assert num_multichar_punc == 0
#
#    def test_fake_punc_tokens_reverse_find(self):
#        # find the closing bracket
#        position = None
#        for i, token in enumerate(self.tokens):
#            ttype, tvalue = token
#            if tvalue == '}':
#                position = i
#
#        x, y = self.positions[position]
#        assert (x, y) == (0, 2) # } on last line
#
#        # start at the closing } and trace back to the {
#        punc_tokens = fake_punc_tokens_reverse(self.tokens,
#                                       self.positions,
#                                       position,
#                                       0)
#        found = False
#        for ttype, tvalue, pos, offset in punc_tokens:
#            if ttype is Token.Punctuation and tvalue == '{':
#                found = True
#                break
#        assert found == True
#
#        x, y = self.positions[pos]
#        x = x + offset
#        assert (x, y) == (29, 0) # { on first line


#View.calculate_brackets
#View.execute_action
