import os
import unittest
import tempfile
from nose.tools import *
from ni.core.colourscheme import load_colourscheme
from ni.core.colourscheme import load_colourscheme_from_lines
from ni.core.colourscheme import load_colourschemes_from_dir
from ni.core.colourscheme import is_alias, is_hexcolour, Colourscheme


# is_alias

def test_is_alias():
    assert is_alias('keyword')

def test_is_not_alias():
    assert is_alias('non-existant') == False

def test_is_not_alias_int():
    assert is_alias(1) == False


# is_hexcolour

def test_is_hexcolour_lowercase():
    assert is_hexcolour('#ffffff')

def test_is_hexcolour_uppercase():
    assert is_hexcolour('#FFFFFF')

def test_is_not_hexcolour_at_all():
    assert is_hexcolour('maap') == False

def test_is_not_hexcolour_hash():
    assert is_hexcolour('FFFFFF') == False

def test_is_not_hexcolour_length():
    assert is_hexcolour('#FFFFF') == False


# Colourscheme

def test_create():
    c = Colourscheme('test')

def test_get_colour_for_modes():
    c = Colourscheme('test')
    for mode in 'default python unknown'.split(' '):
        yield get_colour_for_mode, c, mode

def get_colour_for_mode(c, mode):
    d = c.get_colour_for_mode(mode, 'keyword')
    for k in 'hex bold italic'.split(' '):
        assert d.has_key(k) # check if it contains all the right keys

def test_get_colours_for_modes():
    c = Colourscheme('test')
    for mode in 'default python unknown'.split(' '):
        yield get_colours_for_mode, c, mode

def get_colours_for_mode(c, mode):
    colours = c.get_colours_for_mode(mode)
    assert colours['keyword'].has_key('hex') # just check one random colourname


class TestColourscheme(unittest.TestCase):
    def setUp(self):
        lines = """
        [[default]]
        fg: #222222
        bg: #ffffff
        keyword: #000000 bold
        comment: #999999
        number: fg

        [[python]]
        keyword: #223344
        comment: #cccccc italic
        """.strip().splitlines()

        self.lines = [l.strip() for l in lines]

    # test loading functions

    def test_load_colourscheme_from_lines(self):
        c = load_colourscheme_from_lines('test', self.lines)
        colours = c.get_colours_for_mode('python')
        assert colours['keyword']['hex'] == '#223344'

    def test_load_colourscheme(self):
        #fle = tempfile.NamedTemporaryFile(suffix='.colourscheme', mode='w', delete=False)
        #filename = fle.name
        fid, filename = tempfile.mkstemp(suffix='.colourscheme', text=True)
        fle = open(filename, 'w')
        nameonly = os.path.basename(filename)
        name, extension = os.path.splitext(nameonly)
        try:
            fle.write('\n'.join(self.lines))
            fle.close()

            c = load_colourscheme(filename)

            # check that the name was set and the colours loaded
            colours = c.get_colours_for_mode('python')
            assert c.name == name and colours['keyword']['hex'] == '#223344'

        finally:
            os.unlink(filename)

    def load_colourschemes_from_dir(self):
        filenames = []
        dirpath = tempfile.mkdtemp()
        num = 5
        content = '\n'.join(self.lines)

        try:
            # just setup some files
            for x in xrange(num):
                #fle = tempfile.NamedTemporaryFile(suffix='.colourscheme', dir=dirpath, mode='w', delete=False)
                fid, filename = tempfile.mkstemp(suffix='.colourscheme', dir=dirpath, text=True)
                filenames.append(filename)
                fle = open(filename, 'w')
                fle.write(content)
                fle.close()

            colourschemes = load_colourschemes_from_dir(dirpath)

            # checking if the colourschemes loaded is a bit messy:

            # make sure we have as many as wrote
            assert len(colourschemes) == num

            for c in colourschemes:
                # just make sure it at least has a name
                name = c.name
                colours = c.get_colours_for_mode('python')

                # check that the colours loaded
                assert colours['keyword']['hex'] == '#223344'
        finally:
            for filename in filenames:
                os.unlink(filename)
            os.rmdir(dirpath)

    # test colour parsing and inheritance

    def test_default_colour(self):
        c = load_colourscheme_from_lines('test', self.lines)
        colours = c.get_colours_for_mode('default')
        # check that the python mode didn't affect default colours
        assert colours['keyword']['hex'] == '#000000'
        assert colours['keyword']['bold']

    def test_colour_override(self):
        c = load_colourscheme_from_lines('test', self.lines)
        colours = c.get_colours_for_mode('python')
        assert colours['keyword']['hex'] == '#223344'
        # default specified bold, python doesn't
        assert colours['keyword']['bold'] == False

    def test_colour_override_attr(self):
        c = load_colourscheme_from_lines('test', self.lines)
        colours = c.get_colours_for_mode('python')
        assert colours['comment']['hex'] == '#cccccc'
        # default didn't specify italic, python does
        assert colours['comment']['italic']
