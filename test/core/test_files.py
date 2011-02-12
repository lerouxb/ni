import random
import os
import re
import unittest
import tempfile
import shutil
from nose.tools import *
from ni.core.files import files_first, glob_match, is_textfile, is_text, \
    load_textfile, filtered_files, BinaryFile


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
    """.strip().encode('utf8')

def make_binary_data():
    # make a random byte stream
    s = ''
    for x in xrange(1000):
        char = random.randint(0, 255)
        s += chr(char)
    return s

BINARY_DATA = make_binary_data()


def test_is_text_true():
    assert is_text(TEXT_DATA) == True

def test_is_text_false():
    assert is_text(BINARY_DATA) == False


class TestFiles(unittest.TestCase):
    def setUp(self):
        # create a directory
        self.rootpath = tempfile.mkdtemp()

        # create a text file
        handle, name = tempfile.mkstemp(dir=self.rootpath, text=True,
                                     prefix='text')
        self.textfilename = name
        fle = open(name, 'w')
        fle.write(TEXT_DATA)
        fle.close()

        # create a binary file
        handle, name = tempfile.mkstemp(dir=self.rootpath, text=False,
                                     prefix='binary')
        self.binaryfilename = name
        fle = open(name, 'wb')
        fle.write(BINARY_DATA)
        fle.close()

        # create a hidden directory
        self.hiddendir = tempfile.mkdtemp(dir=self.rootpath, prefix='.a')

        # create a file inside the hidden directory
        handle, name = tempfile.mkstemp(dir=self.hiddendir, text=True,
                                     prefix='settings')
        self.settingsfilename = name

        # create a subdirectory
        self.subdir = tempfile.mkdtemp(dir=self.rootpath, prefix='sub')

        # create some files in the subdirectory
        self.subdirfilenames = []
        for x in xrange(3):
            handle, name = tempfile.mkstemp(dir=self.subdir, text=True, prefix=str(x))
            self.subdirfilenames.append(name)

    def tearDown(self):
        shutil.rmtree(self.rootpath)

    # files_first

    def test_files_first(self):
        prefixes = 'binary text .a sub'.split(' ')
        output = [f for f in files_first(self.rootpath)]

        assert len(prefixes) == len(output)

        for prefix, filename in zip(prefixes, output):
            assert filename.startswith(prefix)

    # glob_match

    def test_glob_match_with_slash_true(self):
        assert glob_match(self.textfilename, '*/text*')

    def test_glob_match_with_slash_false(self):
        # there is ofcourse an incredibly low probability of a temp dir name
        # being created that happens to match
        assert glob_match(self.textfilename, '*/binary*') == False

    def test_glob_match_without_slash_true(self):
        assert glob_match(self.textfilename, 'text*')

    def test_glob_match_without_slash_false(self):
        assert glob_match(self.textfilename, 'binary*') == False

    # is_textfile

    def test_is_textfile_true(self):
        assert is_textfile(self.textfilename)

    def test_is_textfile_false(self):
        assert is_textfile(self.binaryfilename) == False

    # load_textfile

    def test_load_textfile(self):
        # load_textfile(filename)
        data = load_textfile(self.textfilename)
        text = data['content']
        assert isinstance(text, unicode)
        assert text == TEXT_DATA

        assert data['encoding'] == 'utf8'
        assert data['linesep'] == '\n'

    # TODO: test other codecs here

    @raises(BinaryFile)
    def test_load_textfile_fail(self):
        data = load_textfile(self.binaryfilename)

    # filtered_files

    def test_filtered_files_all(self):
        prefixes = 'text settings 0 1 2'.split(' ')

        output = []
        for filename in filtered_files(self.rootpath, self.rootpath,
                                       [], [], False):
            output.append(filename)

        # make sure the filenames start with prefixes in the expected order
        assert len(prefixes) == len(output)
        for prefix, filename in zip(prefixes, output):
            assert os.path.basename(filename).startswith(prefix)

    def test_filtered_files_without_hidden(self):
        prefixes = 'text 0 1 2'.split(' ')

        output = []
        for filename in filtered_files(self.rootpath, self.rootpath,
                                       [], [], True):
            output.append(filename)

        # make sure the filenames start with prefixes in the expected order
        assert len(prefixes) == len(output)
        for prefix, filename in zip(prefixes, output):
            assert os.path.basename(filename).startswith(prefix)

    def test_filtered_files_match_func(self):
        def starts_with_digit(filename):
            # dummy match function that matches filenames that start with
            # a digit
            if os.path.basename(filename)[0].isdigit():
                return True
            return False

        prefixes = '0 1 2'.split(' ')
        output = []
        for filename in filtered_files(self.rootpath, self.rootpath,
                                       [], [], True, starts_with_digit):
            output.append(filename)

        # make sure the filenames start with prefixes in the expected order
        assert len(prefixes) == len(output)
        for prefix, filename in zip(prefixes, output):
            assert os.path.basename(filename).startswith(prefix)

    def test_filtered_files_exclude_globs(self):
        prefixes = 'text'.split(' ')

        output = []
        for filename in filtered_files(self.rootpath, self.rootpath,
                                       ['sub*'], [], True):
            output.append(filename)

        # make sure the filenames start with prefixes in the expected order
        assert len(prefixes) == len(output)
        for prefix, filename in zip(prefixes, output):
            assert os.path.basename(filename).startswith(prefix)

    def test_filtered_files_exclude_regulars(self):
        # filtered_files(rootpath, dirpath, exclude_globs, exclude_regulars, exclude_hidden, match_func)
        prefixes = 'text 2'.split(' ')

        reg_str = '.*\/0.*'             # not compiled yet
        reg_obj = re.compile('.*\/1.*') # already compiled

        output = []
        for filename in filtered_files(self.rootpath, self.rootpath,
                                       [], [reg_str, reg_obj], True):
            output.append(filename)

        # make sure the filenames start with prefixes in the expected order
        assert len(prefixes) == len(output)
        for prefix, filename in zip(prefixes, output):
            assert os.path.basename(filename).startswith(prefix)
