import os
import re
from ni.core.text import slugify
from ni.core.files import glob_match, filtered_files, path_matches


# for loading and saving:
STR = 1
LIST = 2
TUPLES = 3
FORMAT = {
    'name': STR,
    'root-path': STR,
    'exclude-globs': LIST,
    'exclude-regulars': LIST,
    'filter-globs': TUPLES,
    'filter-regulars': TUPLES
}

NON_TRAILING = re.compile("^((\\\ )|[^\ ])+", re.UNICODE)

def strip_trailing(s):
    try:
        return NON_TRAILING.match(s).group(0)
    except AttributeError:
        return s

class WorkspaceNotFound(Exception):
    pass

class WorkspaceImproperlyConfigured(Exception):
    pass

class InvalidFilter(Exception):
    pass

class Workspace(object):
    def __init__(self, workspaces_dir, name, root_path, exclude_globs=None,
                 exclude_regulars=None, filter_globs=None,
                 filter_regulars=None):
        self.workspaces_dir = workspaces_dir
        self.name = name
        self.root_path = root_path
        self.exclude_globs = exclude_globs if exclude_globs else []
        self.exclude_regulars = exclude_regulars if exclude_regulars else []
        self.filter_globs = dict(filter_globs) if filter_globs else {}
        self.filter_regulars = dict(filter_regulars) if filter_regulars else {}

        self.old_slug = self.slug # so we can detect a rename in save()

    def fix_path(self, path):
        path = path[len(self.root_path):]
        if path and path[0] == os.path.sep: # root
            path = path[1:]
        return path

    def get_slug(self):
        return slugify(self.name)
    slug = property(get_slug)

    def contains(self, path, skip_hidden=True):       
        kwargs = {
            'rootpath': self.root_path,
            'exclude_globs': self.exclude_globs,
            'exclude_regulars': self.exclude_regulars,
            'exclude_hidden': skip_hidden
        }
        return path_matches(path, **kwargs)

    def filepaths(self, named_filtr=None, glob_filter=None, re_filter=None,
                  skip_hidden=True):

        kwargs = {
            'rootpath': self.root_path,
            'dirpath': self.root_path,
            'exclude_globs': self.exclude_globs,
            'exclude_regulars': self.exclude_regulars,
            'exclude_hidden': skip_hidden
        }

        if named_filtr:
            if self.filter_globs.has_key(named_filtr):
                pattern = self.filter_globs[named_filtr]
                kwargs['match_func'] = lambda s: glob_match(s, pattern)

            elif self.filter_regulars.has_key(named_filtr):
                pattern = re.compile(self.filter_regulars[named_filtr])
                kwargs['match_func'] = lambda s: bool(pattern.match(s))

            else:
                raise InvalidFilter(named_filtr)

        elif glob_filter:
            kwargs['match_func'] = lambda s: glob_match(s, glob_filter)

        elif re_filter:
            kwargs['match_func'] = lambda s: bool(re_filter.match(s))

        for f in filtered_files(**kwargs):
            yield f

    def save(self):
        success = False

        out = (
            ('name', self.name),
            ('root-path', self.root_path),
            ('exclude-globs', self.exclude_globs),
            ('exclude-regulars', self.exclude_regulars),
            ('filter-globs', self.filter_globs),
            ('filter-regulars', self.filter_regulars),
        )

        workspace_path = os.path.join(self.workspaces_dir, self.slug)

        # is this really the best place for this?
        dirpath = os.path.dirname(workspace_path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        fle = file(workspace_path, "w")

        try:
            for k, v in out:
                mode = FORMAT[k]
                if mode == STR:
                    line = u"%s: %s\n" % (k, v)
                    fle.write(line.encode('utf8'))

                elif mode == LIST:
                    line = u"%s:\n" % (k,)
                    fle.write(line.encode('utf8'))
                    for v1 in v:
                        line = u'    %s\n' % (v1,)
                        fle.write(line.encode('utf8'))

                elif mode == TUPLES:
                    line = u"%s:\n" % (k,)
                    fle.write(line.encode('utf8'))
                    for k1, v1 in v.iteritems():
                        line = u'    %s: %s\n' % (k1, v1)
                        fle.write(line.encode('utf8'))

            success = True

        finally:
            fle.close()

        # if this is a rename, delete the old file
        if success and self.old_slug and self.old_slug != self.slug:
            old_path = os.path.join(self.workspaces_dir, self.old_slug)
            os.unlink(old_path)

    def delete(self):        
        workspace_path = os.path.join(self.workspaces_dir, self.slug)
        os.unlink(workspace_path)

def load_workspace(workspace_path):
    if not os.path.exists(workspace_path):
        raise WorkspaceNotFound(slug)

    data = {
    'name': '',
    'root-path': '',
    'exclude-globs': [],
    'exclude-regulars': [],
    'filter-globs': [],
    'filter-regulars': []
    }

    fle = open(workspace_path)
    try:
        try:
            mode = STR
            variable = ''
            value = ''
            for num, line in enumerate(fle):
                line = line.strip('\n')
                if line[0] == '#':
                    continue

                line = line.decode('utf8')
                if line[:4] == '    ':
                    if mode == LIST:
                        v = strip_trailing(line.lstrip(' '))
                        #print "'%s'" % (v,)
                        data[variable].append(v)

                    elif mode == TUPLES:
                        l = line.lstrip(' ')
                        bits = l.split(':', 1)
                        k = bits[0]
                        if len(bits) > 1:
                            v = strip_trailing(bits[1].lstrip(' '))
                            #print "'%s'" % (v,)
                        else:
                            v = ''

                        if v: # don't add blank ones
                            data[variable].append((k, v))

                    else:
                        raise WorkspaceImproperlyConfigured(slug,
                            "line %s: indent not expected" % (num,))
                else:
                    bits = line.split(":", 1)
                    variable = bits[0]
                    if len(bits) > 1:
                        value = strip_trailing(bits[1].lstrip(' '))
                    else:
                        value = ''
                    if not FORMAT.has_key(variable):
                        raise WorkspaceImproperlyConfigured(slug,
                            "line %s: unknown key '%s'" % (num, variable))
                    mode = FORMAT[variable]
                    if mode == STR:
                        data[variable] = value

            for k, v in data.iteritems():
                if FORMAT[k] == STR and not v:
                    raise WorkspaceImproperlyConfigured(slug,
                        "'%s' is required." % (k,))

        except WorkspaceImproperlyConfigured:
            raise
        except Exception, e:
            print e
        except:
            raise WorkspaceImproperlyConfigured(slug, "unknown error")

    finally:
        fle.close()

    d = {}
    for k, v in data.iteritems():
        d[k.replace('-', '_')] = v
    #print d
    workspaces_dir = os.path.dirname(workspace_path)
    w = Workspace(workspaces_dir, **d)
    return w


