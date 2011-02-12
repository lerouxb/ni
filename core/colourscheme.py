import os


COLOURNAMES = set([
    'bg', 'fg', 'sel', 'current', 'error', 'keyword', 'number', 'literal',
    'symboloperator', 'wordoperator', 'comment', 'comment', 'exception',
    'other', 'plain', 'name', 'function', 'class', 'tag', 'attribute',
    'punctuation', 'generic', 'builtin', 'pseudo', 'self', 'guide', 'gutter_bg',
    'gutter_line', 'gutter_current', 'gutter_fifth', 'gutter_plain'
])

DEFAULT_FG = '#222222'
DEFAULT_BG = '#ffffff'


def load_colourscheme(filepath):
    """
    Load a colourscheme from a file.
    """

    name = os.path.basename(filepath)[:-13]
    fle = open(filepath)
    try:
        colourscheme = load_colourscheme_from_lines(name, fle)
    finally:
        fle.close()
    return colourscheme

def load_colourscheme_from_lines(name, lines):
    """
    Setup a Colourscheme object based on a sequence of lines.

    * The default mode is 'default'.

    * '[[mode]]' type lines switches the current mode.

    * 'colourname: #000000 bold italic' lines specify a colour.
      (bold and italic is optional)
    """

    colourscheme = Colourscheme(name)

    mode = 'default'

    for line in lines:
        line = line.strip()

        if not line or line[0] == '#':
            # skip empty lines and comments
            continue

        if line[:2] == '[[' and line[-2:] == ']]':
            # change mode
            mode = line[2:-2].strip()
            if not colourscheme.modes.has_key(mode):
                colourscheme.modes[mode] = {}
        else:
            bits = line.split(':', 1)
            if len(bits) == 2:
                # this is a colour definition
                # (the actual colour spec and aliases only gets
                #  parsed later in get_colour_for_mode().)
                k = bits[0].strip()
                v = bits[1].strip()
                colourscheme.modes[mode][k] = v

    return colourscheme

def load_colourschemes_from_dir(dirpath):
    """
    Load all files in dirpath with .colourscheme extension as colourschemes.

    Will return a list of Colourscheme objects.
    """

    colourschemes = {}

    filenames = os.listdir(dirpath)
    filenames.sort()
    for filename in filenames:
        if filename.endswith('.colourscheme'):
            fullpath = os.path.join(dirpath, filename)
            colourschemes[filename] = load_colourscheme(fullpath)

    return colourschemes

def is_alias(value):
    """
    Check that value is a known colour name.
    """

    return value in COLOURNAMES

def is_hexcolour(value):
    """
    Check that value is a hash followed by 6 hexadecimal digits.
    """

    if value and isinstance(value, basestring):
        value = value.lower()
        if value[0] != '#':
            return False
        else:
            hexpart = value[1:]
            if len(hexpart) != 6:
                return False
            allowed = set('01234567890abcdef')
            for l in hexpart:
                if not l in allowed:
                    return False
    return True

class Colourscheme(object):
    def __init__(self, name):
        self.name = name
        self.modes = {'default': {}}
        self.cached_colours = {}

    def get_colour_for_mode(self, mode, colourname, previous=None):
        """
        Return a dict with hex, bold and italic as keys.

        Try and lookup colourname in the modes. It will try the specific mode,
        then the default mode, then just use a default colour.

        This is where we actually parse the colour "lines".
        """

        # colourname is the alias like fg, bg, keyword, number, etc.
        # colour is the entire line which is either:
        #     - an alias,
        #     - or a hexcolour bold italic (where bold and italic are optional)
        # hexcolour is a hash followed by 6 hexadecimal digits

        if self.modes.has_key(mode) and self.modes[mode].has_key(colourname):
            # try specific mode
            colour = self.modes[mode][colourname]
        elif mode != 'default' and self.modes['default'].has_key(colourname):
            # ...then try default mode
            colour = self.modes['default'][colourname]
        elif colourname == 'bg':
            # ...then use DEFAULT_BG for bg
            colour = DEFAULT_BG
        else:
            # ...otherwise just use DEFAULT_FG as a last resort
            colour = DEFAULT_FG

        if is_alias(colour):
            # recurse for alias lookup

            if previous == None:
                previous = set()
            if not (colourname in previous):
                # Simple check to not go into a loop
                previous.add(colourname)
                return self.get_colour_for_mode(mode,
                                                colour,
                                                previous=previous)

            elif colourname == 'bg':
                # if we had an alias loop, default bg colours to DEFAULT_BG...
                colour = DEFAULT_BG

            else:
                # ...and other colours to DEFAULT_FG
                colour = DEFAULT_FG

        # just some defaults in case is_hexcolour below returns False
        if colour == 'bg':
            hex_colour = DEFAULT_BG
        else:
            hex_colour = DEFAULT_FG

        bold = False
        italic = False

        bits = colour.split(' ')
        if len(bits):
            # note that the order doesn't matter for bold and italic, but the
            # colour has to be specified first.
            h = bits[0].lower()
            if is_hexcolour(h):
                hexcolour = h
            if 'bold' in bits:
                bold = True
            if 'italic' in bits:
                italic = True

        return {'hex': hexcolour, 'bold': bold, 'italic': italic}

    def get_colours_for_mode(self, mode):
        """
        Get the colours as a dict of dicts for the specified mode.

        So scheme.get_colours_for_mode('python')['keyword']['hex'] should be a
        a string representing a colour in hexadecimal.

        Also, the colours will be cached per mode.
        """
        if not self.cached_colours.has_key(mode):
            # cache results
            colours = {}
            for colourname in COLOURNAMES:
                colour = self.get_colour_for_mode(mode, colourname)
                colours[colourname] = colour
            self.cached_colours[mode] = colours
        return self.cached_colours[mode]


