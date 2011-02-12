import os
import unittest
import tempfile
from nose.tools import *
from pygments.token import Token
from ni.core.document import Document, load_document, InsertDelta, DeleteDelta


#Hello\nthere\nWhat's up with you?\n\n\n
OFFSETS_STRING = "Hello\nthere\nWhat's up with you?\n\n\n"

def test_cursor_pos_to_offset():
    doc = Document(title="Untitled", content=OFFSETS_STRING)
    assert doc.cursor_pos_to_offset((1, 0)) == 6 

    assert doc.cursor_pos_to_offset((0, 5)) == 5
    assert doc.cursor_pos_to_offset((0, 4)) == 4
    assert doc.cursor_pos_to_offset((0, 0)) == 0
    assert doc.cursor_pos_to_offset((0, 0)) == 0
    
    assert doc.cursor_pos_to_offset((2, 0)) == 12
    assert doc.cursor_pos_to_offset((2, 1)) == 13
    
    assert doc.cursor_pos_to_offset((3, 0)) == 32
    assert doc.cursor_pos_to_offset((4, 0)) == 33
    assert doc.cursor_pos_to_offset((5, 0)) == 34

def test_offset_to_cursor_pos():
    doc = Document(title="Untitled", content=OFFSETS_STRING)

    assert doc.offset_to_cursor_pos(6) == (1, 0)
    assert doc.offset_to_cursor_pos(5) == (0, 5)
    assert doc.offset_to_cursor_pos(4) == (0, 4)
    assert doc.offset_to_cursor_pos(0) == (0, 0)
    assert doc.offset_to_cursor_pos(0) == (0, 0)
    
    assert doc.offset_to_cursor_pos(12) == (2, 0)
    assert doc.offset_to_cursor_pos(13) == (2, 1)
    
    assert doc.offset_to_cursor_pos(32) == (3, 0)
    assert doc.offset_to_cursor_pos(33) == (4, 0)
    assert doc.offset_to_cursor_pos(34) == (5, 0)


def test_line_offsets_insert_blank():
    doc = Document(title="Untitled")
    doc.insert(0, OFFSETS_STRING)
    assert doc.line_offsets == [0, 6, 12, 32, 33, 34]

def test_line_offsets_delete_blank():
    doc = Document(title="Untitled", content=OFFSETS_STRING)
    doc.delete(0, len(doc.content))
    assert doc.line_offsets == [0]
    
def test_line_offsets_insert_start():
    doc = Document(title="Untitled", content=OFFSETS_STRING)
    
    doc.insert(0, "#")
    assert doc.line_offsets == [0, 7, 13, 33, 34, 35]
    
    doc.insert(1, "\n")
    assert doc.line_offsets == [0, 2, 8, 14, 34, 35, 36]

def test_line_offsets_delete_start():
    doc = Document(title="Untitled", content=OFFSETS_STRING)
    
    doc.delete(0, 6)
    assert doc.line_offsets == [0, 6, 26, 27, 28]

def test_line_offsets_insert_middle():
    doc = Document(title="Untitled", content=OFFSETS_STRING)
    
    doc.insert(6, "another line\n")
    assert doc.line_offsets == [0, 6, 19, 25, 45, 46, 47]

def test_line_offsets_delete_middle():
    doc = Document(title="Untitled", content=OFFSETS_STRING)
    
    doc.delete(6, 6)
    assert doc.line_offsets == [0, 6, 26, 27, 28]

def test_line_offsets_insert_end():
    doc = Document(title="Untitled", content=OFFSETS_STRING)

    doc.insert(len(doc.content), "another line\n")    
    assert doc.line_offsets == [0, 6, 12, 32, 33, 47]


#def test_blank_document_location():
#    doc = Document(location='/tmp/test.txt')
#
#    # Read the defaults back:
#    assert doc.encoding == 'utf8'
#    assert doc.linesep == '\n'
#    assert doc.tab_size == 8
#    assert doc.location == '/tmp/test.txt'
#    assert doc.title == None
#    assert doc.description == doc.location
#    assert doc.is_modified == False
#    assert doc.must_relex == False
#    assert doc.get_content() == ''
#    assert doc.num_lines == 0
#
#def test_blank_document_title():
#    doc = Document(title='UNTITLED')
#
#    # Read the defaults back:
#    assert doc.encoding == 'utf8'
#    assert doc.linesep == '\n'
#    assert doc.tab_size == 8
#    assert doc.location == None
#    assert doc.title == 'UNTITLED'
#    assert doc.description == doc.title
#    assert doc.is_modified == False
#    assert doc.must_relex == False
#    assert doc.get_content() == ''
#    assert doc.num_lines == 0
#
#@raises(Exception)
#def test_blank_document_nolocation():
#    d = Document()
#
#class MockSettings(object):
#    def __init__(self):
#        self.tab_size = 8
#
#class TestDocument(unittest.TestCase):
#    def setUp(self):
#        self.settings = MockSettings()
#
#        # Please note:
#        # some of the tests are tied really closely to this test data, so if
#        # you change anything here you'll have to change lots of offsets,
#        # expected output, etc elsewhere
#        self.content = u"""
#def fib():
#    \"\"\"
#    A generator that yields the fibonacci numbers.
#    \"\"\"
#    a, b = 0, 1
#    while 1:
#        yield a
#        a, b = b, a + b
#
## print out the first 10 fibonacci numbers
#for i, x in enumerate(fib()):
#    if i > 9:
#        break
#    print "%s: %s" % (i+1, x)
#        """.strip()
#
#        # create a python file
#        #fle = tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False)
#        fid, self.filename = tempfile.mkstemp(suffix='.py', text=True)
#        fle = open(self.filename, 'w')
#        fle.write(self.content.encode('utf8'))
#        fle.close()
#
#    def tearDown(self):
#        # remove the file created during setup
#        os.unlink(self.filename)
#
#    def test_load_document(self):
#        # load the file we created during setup
#        doc = load_document(self.filename, self.settings)
#
#        # Read things back:
#        assert doc.encoding == 'utf8'
#        assert doc.linesep == '\n'
#        assert doc.tab_size == 8
#        assert doc.location == self.filename
#        assert doc.title == None
#        assert doc.description == self.filename
#        assert doc.is_modified == False
#        assert doc.must_relex == False
#        assert doc.get_content() == self.content
#        assert doc.tokenizer.lexer.name == 'Python'
#
#    def test_initial_tokens(self):
#        doc = load_document(self.filename, self.settings)
#
#        # make sure it did actually tokenize things
#        assert len(doc.tokenizer.tokens) > 1
#
#        # just some spot checks to see if everything got tokenized
#        assert doc.tokenizer.tokens[0] == (Token.Keyword, u'def')
#        assert doc.tokenizer.tokens[-1] == (Token.Text, u'\n')
#
#        # join up all the token values to see if we get the original content
#        # back out
#        bits = []
#        for ttype, tvalue in doc.tokenizer.tokens:
#            bits.append(tvalue)
#        tokencontent = ''.join(bits)
#        # pygments adds extra line-break at the end
#        tokencontent = tokencontent.rstrip()
#        assert tokencontent == self.content
#
#    def test_get_lines_line_from(self):
#        doc = load_document(self.filename, self.settings)
#
#        lines = doc.get_lines(11) # only the last three lines
#
#        expected_lines = [
#            '    if i > 9:',
#            '        break',
#            '    print "%s: %s" % (i+1, x)'
#        ]
#
#        assert lines == expected_lines
#
#    def test_get_lines_line_from_line_to(self):
#        doc = load_document(self.filename, self.settings)
#
#        lines = doc.get_lines(11, 13)
#        expected_lines = [
#            '    if i > 9:',
#            '        break'
#        ]
#
#        assert lines == expected_lines
#
#    def test_invalidate(self):
#        doc = load_document(self.filename, self.settings)
#
#        doc.invalidate(0)
#        assert doc.must_relex == True
#
#    def test_get_line(self):
#        doc = load_document(self.filename, self.settings)
#        line = doc.get_line(0)
#
#        assert line == u'def fib():'
#
#    def test_set_line(self):
#        doc = load_document(self.filename, self.settings)
#        line = doc.get_line(0)
#        new_line = '#'+line
#        doc.set_line(0, new_line)
#        line = doc.get_line(0)
#
#        assert line == u'#def fib():'
#
#    def test_is_modified(self):
#        doc = load_document(self.filename, self.settings)
#        new_line = '#'+doc.get_line(0)
#        doc.set_line(0, new_line)
#
#        assert doc.is_modified == True
#
#    def test_save(self):
#        doc = load_document(self.filename, self.settings)
#        new_line = '#'+doc.get_line(0)
#        doc.set_line(0, new_line)
#
#        doc.save()
#
#        new_doc = load_document(self.filename, self.settings)
#        assert new_doc.get_content() == '#'+self.content
#
#    def test_insert_one_line(self):
#        doc = load_document(self.filename, self.settings)
#        doc.insert((13, 11), ' # only first 10!')
#
#        line = doc.get_line(11)
#        assert line == u'    if i > 9: # only first 10!'
#
#        # make sure the next line didn't change
#        line = doc.get_line(12)
#        assert line == u'        break'
#
#    def test_insert_multiple_lines(self):
#        doc = load_document(self.filename, self.settings)
#        text = u'# this requires a\n    # very long explanation\n    '
#        doc.insert((4, 4), text)
#
#        lines = doc.get_lines(4, 7)
#        expected_lines = [
#            u'    # this requires a',
#            u'    # very long explanation',
#            u'    a, b = 0, 1',
#        ]
#
#        assert lines == expected_lines
#
#    def test_delete_one_line(self):
#        doc = load_document(self.filename, self.settings)
#        start = (1, 9)
#        end = (11, 9)
#        doc.delete(start, end)
#
#        line = doc.get_line(9)
#        assert line == '# the first 10 fibonacci numbers'
#
#        line = doc.get_line(10)
#        assert line == 'for i, x in enumerate(fib()):'
#
#    def test_delete_multiple_lines(self):
#        doc = load_document(self.filename, self.settings)
#        start = (23, 4)
#        end = (29, 10)
#        doc.delete(start, end)
#
#        lines = doc.lines
#
#        expected_lines = [
#            u'def fib():',
#            u'    """',
#            u'    A generator that yields the fibonacci numbers.',
#            u'    """',
#            u'    a, b = 0, 1',
#            u'    if i > 9:',
#            u'        break',
#            u'    print "%s: %s" % (i+1, x)'
#        ]
#
#        assert lines == expected_lines
#
#    def test_update_tokens_to_end(self):
#        doc = load_document(self.filename, self.settings)
#
#        scroll_pos = (0, 0)
#        size = (80, 24)
#
#        doc.insert((0, 0), "# hello\n")
#        doc.invalidate(0)
#        doc.update_tokens(scroll_pos, size, True)
#
#        # spot checks
#        assert doc.tokenizer.tokens[0] == (Token.Comment, u'# hello')
#        assert doc.tokenizer.tokens[1] == (Token.Text, u'\n')
#        assert doc.tokenizer.tokens[2] == (Token.Keyword, u'def')
#
#    def test_update_some_tokens(self):
#        doc = load_document(self.filename, self.settings)
#
#        scroll_pos = (0, 0)
#        size = (80, 4) # only 4 lines
#
#        doc.insert((0, 0), "# hello\n")
#        doc.invalidate(0)
#        doc.update_tokens(scroll_pos, size, False)
#
#        # spot checks
#        assert doc.tokenizer.tokens[0] == (Token.Comment, u'# hello')
#        assert doc.tokenizer.tokens[1] == (Token.Text, u'\n')
#        assert doc.tokenizer.tokens[2] == (Token.Keyword, u'def')
#
#        bits = []
#        for ttype, tvalue in doc.tokenizer.tokens:
#            bits.append(tvalue)
#        content = ''.join(bits)
#
#        expected_content = u"# hello\ndef fib():\n    \"\"\"\n    A generator that yields the fibonacci numbers.\n"
#
#        assert content == expected_content
#
#    def test_get_normalized_tokens(self):
#        doc = load_document(self.filename, self.settings)
#
#        tokens = doc.tokenizer.get_normalized_tokens(2, 4)
#        bits = []
#        for ttype, tvalue in tokens:
#            bits.append(tvalue)
#        content = ''.join(bits)
#
#        # hmm. shouldn't there be a \n at the end?
#        expected_content = "    A generator that yields the fibonacci numbers.\n    \"\"\"\n    a, b = 0, 1\n    "
#
#        assert content == expected_content
#
#    def test_SetLineDelta(self):
#        line = u"Yield the fibonacci numbers."
#
#        doc = load_document(self.filename, self.settings)
#        delta = SetLineDelta(doc, 2, line)
#
#        # do
#        delta.do()
#
#        # check modified
#        assert doc.is_modified
#
#        # check content
#        assert doc.get_line(2) == line
#
#        # undo
#        delta.undo()
#
#        # check modified
#        assert not doc.is_modified
#
#        # check content
#        assert doc.get_content() == self.content
#
#    def test_InsertDelta(self):
#        doc = load_document(self.filename, self.settings)
#        text = u'# this requires a\n    # very long explanation\n    '
#        delta = InsertDelta(doc, (4, 4), text)
#
#        # do
#        delta.do()
#
#        # check modified
#        assert doc.is_modified
#
#        # check content
#        lines = doc.get_lines(4, 7)
#        expected_lines = [
#            u'    # this requires a',
#            u'    # very long explanation',
#            u'    a, b = 0, 1'
#        ]
#
#        print lines
#
#        assert lines == expected_lines
#
#        # undo
#        delta.undo()
#
#        # check modified
#        assert not doc.is_modified
#
#        # check content
#        assert doc.get_content() == self.content
#
#    def test_DeleteDelta(self):
#        doc = load_document(self.filename, self.settings)
#        delta = DeleteDelta(doc, (23, 4), (29, 10))
#
#        # do
#        delta.do()
#
#        # check modified
#        assert doc.is_modified
#
#        # check content
#        lines = doc.lines
#
#        expected_lines = [
#            u'def fib():',
#            u'    """',
#            u'    A generator that yields the fibonacci numbers.',
#            u'    """',
#            u'    a, b = 0, 1',
#            u'    if i > 9:',
#            u'        break',
#            u'    print "%s: %s" % (i+1, x)'
#        ]
#
#        assert lines == expected_lines
#
#        # undo
#        delta.undo()
#
#        # check modified
#        assert not doc.is_modified
#
#        # check content
#        assert doc.get_content() == self.content

