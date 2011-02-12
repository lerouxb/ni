import os
import re
import fnmatch
import string
import sys
import chardet


def files_first(path):
    """
    Yield the contents of path files first, then directories, alphabetical.
    """

    filenames = os.listdir(path)
    filenames.sort()

    for filename in filenames:
        if os.path.isfile(os.path.join(path, filename)):
            yield filename
    for filename in filenames:
        if os.path.isdir(os.path.join(path, filename)):
            yield filename

def glob_match(path, pattern):
    """
    Do a "glob-style" match on path using pattern.

    If there is a '/' in pattern, then it matches against the entire path,
    otherwise it just matches against the filename component
    """

    if os.path.sep in pattern:
        search = path
    else:
        # this way you can search for "view.py" without typing "*/view.py"
        search = os.path.basename(path)
    return fnmatch.fnmatch(search, pattern)

class BinaryFile(Exception):
    """
    Thrown when a binary file was encountered and a text file was expected.
    """

    pass

# http://code.activestate.com/recipes/173220/

TEXT_CHARACTERS = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
_NULL_TRANS = string.maketrans("", "")
BLOCKSIZE = 512

def is_textfile(filename, blocksize=BLOCKSIZE):
    """
    Read the first blocksize bytes from the file and analyse it with is_text.
    """

    try:
        fle = open(filename)
        try:
            block = fle.read(blocksize)
        finally:
            fle.close()
    except:
        # Should we do something with the error rather?
        # Is it best to wrap these errors or should the calling code figure
        # it out?
        raise
    return is_text(block)

def is_text(s):
    """
    Return True if something looks like text, False otherwise

    Something is text if it is empty or it doesn't contain character zero and
    it has less than 30% "non-text characters" (see TEXT_CHARACTERS above)
    """

    if "\0" in s:
        return False

    if not s:  # Empty files are considered text
        return True

    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = s.translate(_NULL_TRANS, TEXT_CHARACTERS)

    # If more than 30% non-text characters, then
    # this is considered a binary file
    if float(len(t))/len(s) > 0.30:
        return False
    return True

def load_textfile(filename):
    """
    Return a dict with 'content`', 'encoding', 'linesep' as keys.

    'content' is unicode
    'encoding' is something you can use with str.decode() or unicode.encode()
    'linesep' is '\r', '\r\n' or '\n'

    Will raise:
    BinaryFile() if the file doesn't look like text (see is_text())
    """

    fle = open(filename, 'rU')
    try:
        # first, only read the first BLOCKSIZE bytes so we can analyse it
        block = fle.read(BLOCKSIZE)
        if not is_text(block):
            raise BinaryFile()

        # then read up to the end of the file
        text = block + fle.read()

        linesep = fle.newlines

        try:
            # chardet can be quite slow, so just assume utf8 first
            encoding = 'utf8'
            content = text.decode(encoding)

        except UnicodeDecodeError:
            encoding = chardet.detect(text)['encoding']
            try:
                content = text.decode(encoding, 'replace')
            except UnicodeDecodeError:
                # it shouldn't really be possible to reach this
                # since we use 'replace' above..
                print filename
                raise

        return {
            'content': content,
            'encoding': encoding,
            'linesep': linesep,
        }

    finally:
        fle.close()

def filtered_files(rootpath, dirpath, exclude_globs, exclude_regulars,
                   exclude_hidden=False, match_func=None):
    """
    Recurse through directories and yield text files that match match_func.

    It won't descend into directories that match any of exclude_globs or
    exclude_regulars.

    It will exclude files that match any of exclude_globs or exclude_regulars.

    Things match on the path relative to the rootpath. When it gets called
    rootpath and dirpath should be the same, but rootpath stays the same and
    dirpath differs once it recurses.

    When exclude_hidden is set it won't descend into hidden directories and it
    will also skip hidden files.

    """

    # if we're not filtering, just return everything that shouldn't be excluded
    if not match_func:
        match_func = lambda s: True

    # is this really necessary? feels dirty
    if rootpath[-1] != os.path.sep:
        rootpath += os.path.sep
    if dirpath[-1] != os.path.sep:
        dirpath += os.path.sep

    compiled_exclude_regulars = []
    for r in exclude_regulars:
        if hasattr(r, 'match'):
            # already compiled
            compiled_exclude_regulars.append(r)
        else:
            # assume it is a string representing a regular expression
            compiled_exclude_regulars.append(re.compile(r))

    #[re.compile(r) for r in exclude_regulars]

    for name in files_first(dirpath):
        if name[0] == '.' and exclude_hidden:
            continue

        fullpath = dirpath + name
        relativepath = fullpath[len(rootpath):]
        if not any((glob_match(relativepath, p) for p in exclude_globs)) and \
        not any((p.match(relativepath) for p in compiled_exclude_regulars)):
            if os.path.isfile(fullpath):
                if is_textfile(fullpath):
                    if match_func(relativepath):
                        yield fullpath

            elif os.path.isdir(fullpath):
                # recurse
                for p in filtered_files(rootpath, fullpath, exclude_globs,
                                        exclude_regulars, exclude_hidden,
                                        match_func):
                    # The problem here is that deeply nested files get yielded
                    # many times as it bubbles up.
                    # The proposed "yield from" syntax would really help here.
                    yield p

def path_matches(path, rootpath, exclude_globs, exclude_regulars,
                   exclude_hidden=False):
    """
    This is similar to filtered_files, but for determining if a specific path
    would be included or not.
    """

    if not path.startswith(rootpath):
        return False
    
    if not rootpath.endswith(s.path.sep):
        rootpath += os.path.sep
    
    compiled_exclude_regulars = []
    for r in exclude_regulars:
        if hasattr(r, 'match'):
            # already compiled
            compiled_exclude_regulars.append(r)
        else:
            # assume it is a string representing a regular expression
            compiled_exclude_regulars.append(re.compile(r))
    
    relativepath = path[len(rootpath):]
    bits = relativepath.rstrip('/').split('/')
    
    for i in range(len(bits)):
        if bits[i][0] == '.' and exclude_hidden:
            continue
        
        relativepath = '/'.join(bits[:i+1])
        fullpath = rootpath + relativepath
        
        if not any((glob_match(relativepath, p) for p in exclude_globs)) and \
        not any((p.match(relativepath) for p in compiled_exclude_regulars)):
            if os.path.isfile(fullpath):
                if is_textfile(fullpath):
                    pass
                else:
                    # binary files aren't allowed
                    return False
            elif os.path.isdir(fullpath):
                # directories are fine
                pass
            else:
                # not a file or directory, not fine
                return False
        else:
            # this path should be excluded
            return False
    
    return True
