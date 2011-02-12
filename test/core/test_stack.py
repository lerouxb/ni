import unittest
from nose.tools import *
from ni.core.stack import Stack


def test_new_stack():
    s = Stack()
    assert repr(s) == repr([])
    assert str(s) == str([])
    assert unicode(s) == unicode([])
    assert len(s) == len([])

def test_new_stack_sized():
    s = Stack(10)
    assert s.size == 10

def test_stack_push():
    s = Stack()
    s.push(1)
    assert len(s) == 1

def test_stack_last():
    s = Stack()
    s.push(1)
    assert s.last() == 1
    assert len(s) == 1 # the value is still on the stack

def test_stack_push_pop():
    s = Stack()
    s.push(1)
    assert s.pop() == 1
    assert len(s) == 0

def test_stack_push_pop_pop():
    s = Stack()
    s.push(1)
    s.pop()
    assert s.pop() == None # is this really the right thing to do?

def test_stack_clear():
    s = Stack()
    s.push(1)
    s.clear()
    assert len(s) == 0

def test_stack_limit_reached():
    s = Stack(5)
    for x in xrange(5):
        s.push(x)
    assert len(s) == 5
    s.push(5) # 0..4 and now 5
    assert len(s) == 5 # length is still 5
