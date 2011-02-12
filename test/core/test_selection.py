import unittest
from nose.tools import *
from ni.core.document import Document
from ni.core.selection import Selection


LINES = u"""
def fib():
    \"\"\"
    A generator that yields the fibonacci numbers.
    \"\"\"
    a, b = 0, 1
    while 1:
        yield a
        a, b = b, a + b

# print out the first 10 fibonacci numbers
for i, x in enumerate(fib()):
    if i > 9:
        break
    print "%s: %s" % (i+1, x)
""".strip().split('\n')

#def make_document():
#    doc = Document(title='UNTITLED')
#    doc.insert((0, 0), '\n'.join(LINES))
#    return doc
#
#def test_new_selection_forward():
#    doc = make_document()
#    selection = Selection(doc, (0, 0), (3, 1))
#    assert selection.start == (0, 0)
#    assert selection.end == (3, 1)
#
#    assert unicode(selection) == u"(0, 0) to (3, 1)"
#
#def test_new_selection_backward():
#    doc = make_document()
#    selection = Selection(doc, (3, 1), (0, 0))
#    assert selection.start == (3, 1)
#    assert selection.end == (0, 0)
#
#def test_selection_set_start():
#    doc = make_document()
#    selection = Selection(doc, (3, 1), (0, 0))
#    selection.start = (1, 1)
#    assert selection.start == (1, 1)
#
#def test_selection_set_end():
#    doc = make_document()
#    selection = Selection(doc, (3, 1), (0, 0))
#    selection.end = (2, 4)
#    assert selection.end == (2, 4)
#
#def test_selection_get_normalised():
#    doc = make_document()
#    selection = Selection(doc, (3, 1), (0, 0))
#
#    normalised = selection.get_normalised()
#
#    assert normalised.start == (0, 0)
#    assert normalised.end == (3, 1)
#
#def test_selection_get_content():
#    doc = make_document()
#    selection = Selection(doc, (0, 0), (7, 1))
#
#    assert selection.get_content() == "def fib():\n    \"\"\""
#
#def test_selection_line_in_selection():
#    doc = make_document()
#    selection = Selection(doc, (0, 0), (0, 7))
#    assert selection.line_in_selection(3)
#
#def test_selection_line_in_selection_false():
#    doc = make_document()
#    selection = Selection(doc, (0, 0), (0, 7))
#    assert selection.line_in_selection(8) == False
#
#def test_selection_in_selection():
#    doc = make_document()
#    selection = Selection(doc, (0, 0), (0, 7))
#    assert selection.in_selection((1, 1))
#
#def test_selection_in_selection_false():
#    doc = make_document()
#    selection = Selection(doc, (0, 0), (0, 7))
#    assert selection.in_selection((1, 7)) == False
