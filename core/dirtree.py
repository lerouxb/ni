from itertools import chain
import os


def compare_nodes(a, b):
    if a.path < b.path:
        return -1
    elif a.path > b.path:
        return 1
    else:
        return 0

class Node(object):
    def __init__(self, path):
        self.path = path

    def get_name(self):
        return os.path.basename(self.path.rstrip(os.path.sep))
    name = property(get_name)

class DirNode(Node):
    def __init__(self, path):
        if path[-1] != os.path.sep:
            path += os.path.sep
        super(DirNode, self).__init__(path)
        self.dirs = []
        self.files = []

    def add(self, path):
        dirname = os.path.dirname(path) + os.path.sep
        #print "add:", dirname, self.path
        if dirname == self.path:
            # we reached the end, so add a file
            for filenode in self.files:
                if filenode.path == path:
                    break
            else:
                # don't add duplicates
                self.files.append(FileNode(path))
                self.files.sort(compare_nodes)
        else:
            # We need to either add a directory or the file has to be added to
            # subdirectory of this directory
            path_bits = self.path.strip(os.path.sep).split(os.path.sep)
            new_path_bits = path.strip(os.path.sep).split(os.path.sep)
            # TODO: better root path detection
            if self.path == os.path.sep:
                num_pathbits = 0
            else:
                num_pathbits = len(path_bits)

            bits_remaining = new_path_bits[num_pathbits:]
            name = bits_remaining[0]

            for dirnode in self.dirs:
                if dirnode.name == name:
                    # a node already exists for the required subdir, so add the
                    # path to that
                    dirnode.add(path)
                    break
            else:
                #print "adding a new dir"
                # we need to create a sub-directory and then pass the path to
                # that node
                dirpath = u"/%s" % ("/".join(new_path_bits[:num_pathbits+1]),)
                dirnode = DirNode(dirpath)
                self.dirs.append(dirnode)
                self.dirs.sort(compare_nodes)
                dirnode.add(path)

    def collapse(self):
        if not self.files and len(self.dirs) == 1:
            child = self.dirs[0]
            self.path = child.path
            self.files = child.files
            self.dirs = child.dirs
            # is this necessary?
            #self.files.sort(compare_nodes)
            #self.dirs.sort(compare_nodes)
            self.collapse() # recurse on this directory

        else:
            for node in self.dirs:
                node.collapse() # recurse on the sub directories


    def output(self):
        print self.path
        for node in chain(self.files, self.dirs):
            node.output()

    def walk(self, cb, parent_path=''):
        cb(self, parent_path)

        for node in chain(self.files, self.dirs):
            node.walk(cb, self.path)

class FileNode(Node):
    def get_dirpath(self):
        return os.path.dirname(self.path) + os.path.sep
    dirpath = property(get_dirpath)

    def output(self):
        print self.path

    def walk(self, cb, parent_path=''):
        cb(self, parent_path)

class RootDirNode(DirNode):
    def __init__(self):
        # TODO: better root path detection
        super(RootDirNode, self).__init__(os.path.sep)

