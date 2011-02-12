import os
import codecs
from ni.core.workspace import load_workspace


def load_settings_from_file(filename, klass):
    settings = klass(filename)

    try:
        fle = open(filename)
        try:
            fields = set(settings.fields)
            for line in fle.readlines():
                try:
                    name, value = line.strip().split('=', 1)
                    if name in fields:
                        settings[name] = value
                except ValueError:
                    pass
            return settings

        finally:
            fle.close()

    except IOError:
        pass

    return settings

class BaseSettings(object):
    def __init__(self, filepath):
        self.settings_dir = os.path.dirname(filepath)
        self.filepath = filepath
        self.fields = ['indent_width', 'tab_size', 'file_encoding', 'linesep',
                       'indent_spaces', 'most_recent_file']
        self.field_dict = {}
        self._defaults()

    def _defaults(self):
        # default values
        self.field_dict.update({
            'indent_width': 4,
            'tab_size': 8,
            'file_encoding': 'utf8',
            'linesep': os.linesep,
            'indent_spaces': True,
            'most_recent_file': None
        })

    def __getattr__(self, name):
        if name in self.fields:
            return self.field_dict[name]
        else:
            err = "'%s' object has no attribute '%s'" % (type(self), name)
            raise AttributeError(err)

    def __getitem__(self, k):
        return self.field_dict[k]

    def __setitem__(self, name, value):
        if not name in self.fields:
            raise KeyError("'%s' is not a valid field.")

        validator_name = '_val_'+name
        if hasattr(self, validator_name):
            validator = getattr(self, validator_name)
            value = validator(value)
        self.field_dict[name] = value

    def get_recent_files_path(self):
        return os.path.join(self.settings_dir, 'recent_files')

    def get_workspaces_dir(self):
        return os.path.join(self.settings_dir, 'workspaces')

    #def get_workspace_path(self, slug):
    #    return os.path.join(self.get_workspaces_dir(), slug+'.workspace')

    def load_workspaces(self):
        workspaces = []

        workspaces_dir = self.get_workspaces_dir()
        filenames = os.listdir(workspaces_dir)
        filenames.sort()
        for filename in filenames:
            extension = filename.split('.')[-1]
            if extension == 'workspace':
                slug = filename[:-10]
                workspaces_dir = self.get_workspaces_dir()
                workspace_path = os.path.join(workspaces_dir, slug+'.workspace')
                workspaces.append(load_workspace(workspace_path))

        return workspaces

    def save(self):
        def format(name):
            formatter_name = '_format_'+name
            if hasattr(self, formatter_name):
                formatter = getattr(self, formatter_name)
                return formatter()
            else:
                return self[name]

        text = "# NOTE: This file is managed automatically, so manual " +\
               "changes might be lost.\n"
        text += "\n".join([u"%s=%s" % (f, format(f)) for f in self.fields])
        text += "\n"

        if not os.path.exists(self.settings_dir):
            os.mkdir(self.settings_dir)

        fle = open(self.filepath, "w")
        try:
            fle.write(text)
        finally:
            fle.close()

    # --- validators

    def _val_indent_width(self, value):
        value = int(value)
        if not value in (2, 4, 6, 8):
            raise Exception()
        return value

    def _val_tab_size(self, value):
        value = int(value)
        if not value in (2, 4, 6, 8):
            raise Exception()
        return value

    def _val_indent_spaces(self, value):
        return value in (True, 'True')

    def _val_file_encoding(self, value):
        encoder = codecs.getencoder(value)
        return value

    def _val_linesep(self, value):
        value = value.replace('\\n', '\n').replace('\\r', '\r')
        if not value in ('\n', '\r', '\r\n'):
            raise Exception()
        return value

    def _val_most_recent_file(self, value):
        if value and value != 'None':
            return value
        else:
            return None

    # --- formatters

    def _format_linesep(self):
        value = self.linesep.replace('\n', '\\n').replace('\r', '\\r')
        return value
