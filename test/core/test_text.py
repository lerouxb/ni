import random
import unittest
from nose.tools import *
from ni.core.text import tab_len, char_pos_to_tab_pos, \
    tab_pos_to_char_pos, pad, get_word_range, cap, slugify

from ni.core.document import Document # for position stuff later on
                                      # which should probably be moved to
                                      # another module..

# for position stuff at end
TEXT_DATA = u"""
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
""".strip()

def make_document():
    doc = Document(title='UNTITLED')
    doc.insert(0, TEXT_DATA)
    return doc

def test_tab_len():
    assert tab_len('\t', 8) == 8

def test_char_pos_to_tab_pos():
    assert char_pos_to_tab_pos('\ta', 1, 8) == 8

def test_tab_pos_to_char_pos():
    assert tab_pos_to_char_pos('\ta', 4, 8) == 0

def test_tab_pos_to_char_pos_alternative():
    assert tab_pos_to_char_pos('a\t', 4, 8) == 1

def test_pad():
    s = '\t'
    line = pad(s, 80, 8)
    assert len(line) == 73

def test_get_word_range_word_middle():
    text = "hello there"
    start, end = get_word_range(text, 8) # somewhere inside 'there'
    assert start == 6
    assert end == 11

def test_get_word_range_word_before():
    text = "hello there"
    start, end = get_word_range(text, 6) # just before 'there'
    assert start == 6
    assert end == 11

def test_get_word_range_whitespace():
    text = 'hello there'
    start, end = get_word_range(text, 5) # the space between the words
    assert start == 5
    assert end == 6

def test_get_word_range_symbol():
    text = 'monkey != banana'
    start, end = get_word_range(text, 8) # before the =
    assert start == 7
    assert end == 9

def test_cap_too_small():
    #cap(value, minimum, maximum)
    assert cap(1, 2, 3) == 2

def test_cap_ok():
    #cap(value, minimum, maximum)
    assert cap(2, 1, 3) == 2

def test_cap_too_big():
    #cap(value, minimum, maximum)
    assert cap(4, 1, 3) == 3

def test_slugify():
    text = u'a slug to b\xeb!' # compose "e
    assert slugify(text) == 'a-slug-to-be'

