import time
from nose.tools import *
from ni.core.benchmark import BenchmarkTimer, format_report


def test_create():
    b = BenchmarkTimer()

def test_blank_report():
    b = BenchmarkTimer()
    rows = b.get_report()
    assert len(rows) == 0

@raises(Exception)
def test_end_before_start():
    b = BenchmarkTimer()
    b.end()

def test_start():
    b = BenchmarkTimer()
    b.start("This is a test")

@raises(Exception)
def test_start_twice():
    b = BenchmarkTimer()
    b.start("This is a test")
    b.start("This is a test")

def test_run_one():
    b = BenchmarkTimer()
    b.start("This is a test")
    b.end()

    rows = b.get_report()
    assert len(rows) == 1

def test_run_multiple():
    b = BenchmarkTimer()
    b.start("This is a test")
    b.end()
    b.start("This is another test")
    b.end()

    rows = b.get_report()
    assert len(rows) == 2

def test_report_fields():
    b = BenchmarkTimer()
    b.start("This is a test")
    b.end()
    b.start("This is another test")
    b.end()

    rows = b.get_report()
    first_row = rows[0]

    for k in 'message amount min max avg'.split(' '):
       yield check_report_field, first_row, k

def check_report_field(r, k):
    assert r.has_key(k)

def test_format_report_empty():
    b = BenchmarkTimer()
    rows = b.get_report()
    output = format_report(rows)

    lines = output.split('\n')
    assert len(lines) == 2 # headings, ---

def test_format_report_one():
    b = BenchmarkTimer()

    b.start("This is a test")
    b.end()

    rows = b.get_report()
    output = format_report(rows)

    lines = output.split('\n')
    assert len(lines) == 3 # headings, ---, message

def test_format_report_multiple():
    b = BenchmarkTimer()

    b.start("This is a test")
    b.end()
    b.start("This is another test")
    b.end()

    rows = b.get_report()
    output = format_report(rows)

    lines = output.split('\n')
    assert len(lines) == 4 # headings, ---, message
