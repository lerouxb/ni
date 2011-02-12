import os
import gtk
from ni.core.colourscheme import load_colourschemes_from_dir, \
            Colourscheme
from ni.editors.base.settings import BaseSettings, load_settings_from_file


SETTINGS_DIR      = os.path.join(os.path.expanduser('~'), '.ni')
SETTINGS_FILENAME = 'ni_gtk'
GLADE_DIR         = '/usr/share/ni/glade/'
GLOBAL_COLOURSCHEMES_DIR = '/usr/share/ni/colourschemes/'

def make_bool(val):
    if val == "False":
        return False
    else:
        return bool(val)

class GtkSettings(BaseSettings):
    def __init__(self, filepath=None):
        super(GtkSettings, self).__init__(filepath)

        self.fields += ['font_name', 'font_size', 'right_margin', 'show_gutter',
                        'show_statusbar', 'show_sidebar', 'show_margin',
                        'win_width', 'win_height', 'win_x', 'win_y',
                        'colourscheme', 'workspace']

    def _defaults(self):
        super(GtkSettings, self)._defaults()

        self.field_dict.update({
            'font_name': 'Bitstream Vera Sans Mono',
            'font_size':  9,
            'right_margin':  80,
            'show_gutter':  True,
            'show_statusbar':  True,
            'show_sidebar':  True,
            'show_margin':  True,
            'win_width':  760,
            'win_height':  500,
            'win_x':  0,
            'win_y':  0,
            'colourscheme': 'happy',
            'workspace': None
        })

    def load_colourschemes(self):
        colourschemes = {}

        # global colourschemes
        global_dir = GLOBAL_COLOURSCHEMES_DIR
        if os.path.exists(global_dir) and os.path.isdir(global_dir):
            global_colourschemes = load_colourschemes_from_dir(global_dir)
            colourschemes.update(global_colourschemes)

        # user colourschemes
        settings_dir = self.settings_dir
        user_dir = os.path.join(settings_dir, 'colourschemes')
        if os.path.exists(user_dir) and os.path.isdir(user_dir):
            user_colourschemes = load_colourschemes_from_dir(user_dir)
            # merge them in so that per-user colourschemes override
            # system-wide ones
            colourschemes.update(user_colourschemes)

        # fake default one just in case
        if not colourschemes:
            colourschemes['none.colourscheme'] = Colourscheme('None')

        # maintain alphabetical order
        scheme_order = colourschemes.keys()
        scheme_order.sort()
        scheme_list = [colourschemes[k] for k in scheme_order]

        return scheme_list

    def _val_font_name(self, value):
        v = value.lower()

        context = gtk.Window().get_pango_context()
        families = context.list_families()
        monofonts = [fam for fam in families if fam.is_monospace()]

        for fam in monofonts:
            fam_name = fam.get_name().lower()
            if fam_name == v:
                break
        else:
            raise Exception()

        return value

    def _val_font_size(self, value):
        value = int(value)
        if value < 6 or value > 72:
            raise Exception()
        return value

    def _val_right_margin(self, value):
        value = int(value)
        if value < 1:
            raise Exception()
        return value

    def _val_show_gutter(self, value):
        return make_bool(value)

    def _val_show_statusbar(self, value):
        return make_bool(value)

    def _val_show_sidebar(self, value):
        return make_bool(value)

    def _val_show_margin(self, value):
        return make_bool(value)

    def _val_win_width(self, value):
        return int(value)

    def _val_win_height(self, value):
        return int(value)

    def _val_win_x(self, value):
        return int(value)

    def _val_win_y(self, value):
        return int(value)

def load_gtk_settings():
    settings_filepath = os.path.join(SETTINGS_DIR, SETTINGS_FILENAME)
    return load_settings_from_file(settings_filepath, GtkSettings)

