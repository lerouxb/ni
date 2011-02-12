import re
import os
from threading import Thread
from ni.core.document import Document
from ni.core.files import glob_match, load_textfile, BinaryFile
from ni.core.workspace import filtered_files


#__all__ = ['SEARCH_SELECTION', 'SEARCH_DOCUMENT', 'SEARCH_WORKSPACE',
#           'SEARCH_DIRECTORY', 'InitialSearchThread', 'BulkUpdateSearchThread',
#           'UpdateSearchThread']

SEARCH_SELECTION = 1
SEARCH_DOCUMENT  = 2
SEARCH_DOCUMENTS = 3
SEARCH_WORKSPACE = 4
SEARCH_DIRECTORY = 5


linestart_re = re.compile('^.', re.U|re.M)

def find_line_starts(code):
    line_starts = []
    for match in linestart_re.finditer(code):
        line_starts.append(match.start())
    return line_starts

def get_closest_offset(line_starts, index):
    pass
#    prev_pos = 0
#    for pos in line_starts:
#        if index < pos:
#            return prev_pos
#        else:
#            prev_pos = pos
#    return pos

def simplefinditer(pattern, line):
    start = 0
    length = len(line)
    pattern_length = len(pattern)

    while start < length:
        pos = line.find(pattern, start)
        if pos != -1:
            yield pos, pos+pattern_length
            start = pos+pattern_length
        else:
            break

class InitialSearchThread(Thread):
    def start(self, search):
        self.search = search
        self.interrupted = False

        if search.use_regex:
            # compile the regular expression once
            flags = re.U|re.M
            if self.search.ignore_case:
                flags = flags|re.I
            self.reg = re.compile(search.search_pattern, flags)

        else:
            self.reg = None

        super(InitialSearchThread, self).start()

    def interrupt(self):
        self.interrupted = True

    def search_regex(self, filename, code):
        # cache the starting positions of all the lines in code
        line_starts = find_line_starts(code)

        num_matches = 0

        # do the actual search
        for match in reg.finditer(code):
            if self.interrupted:
                return

            # completely wrong:
            start = match.start()
            end = match.end()
            pos = get_closest_offset(line_starts, start)
            offset = line_starts.index(pos)
            num = offset
            match_text = ''
            search.add_match(filename, match_text, num, start, end)
            num_matches += 1

        return num_matches

    def search_simple(self, filename, code):
        # TODO: what about multi-line?

        num_matches = 0

        search = self.search
        pattern = search.search_pattern
        lines = code.splitlines()

        for num, line in enumerate(lines):
            # TODO:
            #   could be multiple in one line
            start = line.find(pattern)
            if start != -1:
                #print "found a match at", str(num)
                end = start + len(pattern)
                search.add_match(filename, line, num, start, end)
                num_matches += 1

        return num_matches

    def run(self):
        search = self.search

        view = search.view
        workspace = search.workspace
        directory = search.directory
        search_type = search.search_type

        # build the list of files we need to search

        if search_type == SEARCH_SELECTION:
            if view.document.location:
                search.files = set([view.document.location])
            else:
                search.files = set([view.document])

        elif search_type == SEARCH_DOCUMENT:
            if view.document.location:
                search.files = set([view.document.location])
            else:
                search.files = set([view.document])

        elif search_type == SEARCH_DOCUMENTS:
            search.files = set()
            for view in search.editor.views:
                if view.document.location:
                    search.files.add(view.document.location)
                else:
                    search.files.add(view.document)

        elif search_type == SEARCH_WORKSPACE:
            search.files = set()

            if search.workspace_filter_glob:
                pattern = search.workspace_filter_glob
                paths = workspace.filepaths(glob_filter=pattern,
                                            skip_hidden=search.skip_hidden)
            else:
                pattern = search.workspace_filter_regex
                paths = workspace.filepaths(re_filter=pattern,
                                            skip_hidden=search.skip_hidden)

            for filename in paths:
                if self.interrupted:
                    return
                search.files.add(filename)

        elif search_type == SEARCH_DIRECTORY:
            search.files = set()

            # sanity checks
            if not os.path.exists(directory):
                return
            if not os.path.isdir(directory):
                return

            pattern = search.directory_filter

            if search.is_recursive:
                kwargs = {
                    'rootpath': directory,
                    'dirpath': directory,
                    'exclude_globs': [],
                    'exclude_regulars': [],
                    'exclude_hidden': search.skip_hidden
                }
                if pattern:
                    kwargs['match_func'] = lambda s: glob_match(s, pattern)
                else:
                    kwargs['match_func'] = lambda s: True

                for filename in filtered_files(**kwargs):
                    if self.interrupted:
                        return
                    search.files.add(filename)

            else:
                for filename in os.listdir(directory):
                    fullpath = os.path.join(directory, filename)
                    if os.path.isfile(fullpath):
                        if not pattern or glob_match(filename, pattern):
                            search.files.add(fullpath)

        print len(search.files), "files."

        # cache open files / views
        open_files = {}
        for view in search.editor.views:
            if view.document.location:
                open_files[view.document.location] = view
            else:
                # files without locations haven't been saved yet
                open_files[view.document] = view

        if search_type == SEARCH_SELECTION:
            pass # forget about this one for now

        else:
            # go through the files one by one, search
            for fle in search.files:
                if self.interrupted:
                    return

                if isinstance(fle, Document):
                    document = fle
                    path = document.description

                    # this means we're searching an unsaved document
                    if open_files.has_key(document):
                        content = document.content

                    else:
                        continue

                else:
                    filename = fle
                    path = filename

                    # we're searching a document that has a location
                    if open_files.has_key(filename):
                        # read file from memory
                        doc = open_files[filename].document
                        content = doc.content

                    else:
                        # we don't have the file open, so we have to read it
                        # from disk
                        try:
                            try:
                                data = load_textfile(filename)
                                content = data['content']
                            except BinaryFile:
                                # the file appears to be binary, so skip it
                                continue

                        except:
                            raise # TODO: handle error nicely

                print path

                if search.use_regex:
                    found_matches = self.search_regex(path, content)
                else:
                    found_matches = self.search_simple(path, content)

                if found_matches:
                    pass # signal redraw

        search.notify_done()

class BulkUpdateSearchThread(Thread):
    def start(self, search):
        self.search = search
        self.interrupted = False
        super(BulkUpdateSearchThread, self).start()

    def interrupt(self):
        self.interrupted = True

    def run(self):
        search = self.search

        # cache open files / views
        open_files = {}
        for view in search.views:
            if view.document.location:
                open_files[view.document.location] = view

        search.notify_done()

class UpdateSearchThread(Thread):
    def start(self, search):
        self.search = search
        self.interrupted = False
        super(UpdateSearchThread, self).start()

    def interrupt(self):
        self.interrupted = True

#    def run_regex(self):
#        search = self.search
#
#        # compile the regular expression once
#        flags = re.U|re.M
#        if search.ignore_case:
#            flags = flags|re.I
#        reg = re.compile(search.pattern, flags)
#
#        # do stuff, remember to check self.interrupted
#        for filename, linenum in search.changes.iteritems():
#            if self.interrupted:
#                return
#
#            # clear from the specified number
#            search.clear_lines(filename, linenum)
#
#            ####### doc?
#
#            # do multi-line regular expression search
#            code = doc.linesep.join(doc.get_lines(linenum))
#
#            # cache the starting positions of all the lines in code
#            line_starts = find_line_starts(code)
#
#            # do the actual search
#            for match in reg.finditer(code):
#                if self.interrupted:
#                    return
#
#                start = match.start()
#                end = match.end()
#                pos = get_closest_offset(line_starts, start)
#                offset = line_starts.index(pos)
#                num = linenum + offset
#                search.add_match(filename, num, start, end)
#
#    def run_simple(self):
#        search = self.search
#
#        # do stuff, remember to check self.interrupted
#        for filename, linenum in search.changes.iteritems():
#            if self.interrupted:
#                return
#
#            # clear from the specified number
#            search.clear_lines(filename, linenum)
#
#            pattern = search.pattern
#
#            # normalise if we ignore case
#            if search.ignore_case:
#                pattern = pattern.lower()
#
#            for offset, line in enumerate(doc.get_lines(linenum)):
#                if self.interrupted:
#                    return
#
#                # normalise if we ignore case
#                if search.ignore_case:
#                    line = line.lower()
#
#                # search the line
#                for start, end in simplefinditer(pattern, line):
#                    num = linenum+offset
#                    search.add_match(filename, linenum, start, end)

    def run(self):
        search = self.search

        # ONLY UPDATE CURRENT VIEW

        # This is an existing search, so we're only taking changes into
        # consideration.
        # TODO: only do multiline if we have it set?

        if search.use_regex:
            self.run_regex()
        else:
            self.run_simple()

        if not self.interrupted:
            # only clear the changes if we didn't get interrupted
            #search.changes = {}
            # TODO: ONLY REMOVE CURRENT VIEW FROM search.changes
            pass

        search.notify_done()

class Search(object):
    def __init__(self, editor, **kwargs):
        self.editor = editor

        self.search_type = kwargs['search_type']
        self.search_pattern = kwargs['search']
        self.replace_pattern = kwargs['replace']
        self.ignore_case = kwargs['ignore_case']
        self.use_regex = kwargs['use_regex']
        self.skip_hidden = kwargs['skip_hidden']

        self.view = kwargs.get('view', False)
        self.workspace = kwargs.get('workspace', False)
        self.workspace_filter_glob = kwargs.get('workspace_filter_glob', False)
        self.workspace_filter_regex = kwargs.get('workspace_filter_regex', False)
        self.directory = kwargs.get('directory', False)
        self.directory_filter = kwargs.get('directory_filter', False)
        self.is_recursive = kwargs.get('is_recursive', False)

        self.files = set() # list of filenames that match
        self.changes = {}  # dict with filenames as keys and
                           # line numbers as values
                           # (used by update())

        # NOTE: we don't store matches here
        #       (that depends on the specific editor)

        self.thread = None

        # This was moved to the subclass(es)
        #self.thread = InitialSearchThread()
        #self.thread.start(self)

    def notify_file_add(self, filename=None, document=None):
        if not (filename or document):
            return False

        if filename and filename in self.files:
            return False

        if document and document in self.files:
            return False

        if self.search_type == SEARCH_SELECTION:
            return False # new files don't affect selection searches
            #if filename == self.view.document.location:
            #    self.files.add(filename)
            #    self.notify_change(filename)
            #    return True

        elif self.search_type == SEARCH_DOCUMENT:
            return False # new files don't affect document searches
            #if filename == self.view.document.location:
            #    self.files.add(filename)
            #    self.notify_change(filename)
            #    return True

        elif self.search_type == SEARCH_DOCUMENTS:
            if filename:
                self.files.add(filename)
                self.notify_change(filename)
            else:
                self.files.add(document)
                self.notify_change(document)
            return True

        elif self.search_type == SEARCH_WORKSPACE:
            if self.workspace_filter_glob:
                f = self.workspace_filter_glob
                found = self.workspace.contains(filename, glob_filter=f)
            else:
                f = self.workspace_filter_regex
                found = self.workspace.contains(filename, re_filter=f)
            if found:
                self.files.add(filename)
                self.notify_change(filename)
                return True

            #paths = [self.workspace.root_path, filename]
            #if os.path.commonprefix(paths) == self.workspace.root_path:
                #basename = os.path.basename(filename)
                #if glob_match(basename, pattern):
                #    self.files.add(filename)

        elif self.search_type == SEARCH_DIRECTORY:
            paths = [self.directory, filename]
            if os.path.commonprefix(paths) == self.directory:
                basename = os.path.basename(filename)
                if glob_match(basename, pattern):
                    self.files.add(filename)
                    return True

        return False

    def notify_file_remove(self, filename):
        # Not used yet. Maybe dbus one day?
        if filename in self.files:
            self.files.remove(filename)
            return True
        return False

    def clear_lines(self, filename, fromline):
        # called from thread
        # must be overridden in specific editor
        raise NotImplemented()

    def add_match(self, filename, match, linenum, start, end):
        # called from thread
        # must be overridden in specific editor
        raise NotImplemented()

    def notify_change(self, filename, linenum=0):
        # NOTE: filename can now be a document or a file path

        # REMEMBER: deal with selection searches. It is basically impossible to
        #           know what to search once you change things because the
        #           selection is gone and the document changes, so just remove
        #           the search if someone modifies the document it was for?
        #           (alternatively, try and keep it around if the number of
        #            lines don't change? or just add a notice that selection
        #            searches are dodgy?)

        if self.search_type == SEARCH_SELECTION:
            return # for now don't update selection searches at all..

        if filename in self.files:
            if self.changes.has_key(filename):
                self.changes[filename] = min(self.changes[filename], linenum)
            else:
                self.changes[filename] = linenum

    def notify_done(self):
        raise NotImplemented()

    def detach(self):
        raise NotImplemented()

    def can_interrupt(self):
        if self.thread and self.thread.isAlive():
            if isinstance(self.thread, UpdateSearchThread):
                return True
            else:
                # don't interrupt initial searches and bulk updates
                return False
        return True

    def interrupt(self):
        #if self.thread and self.thread.isAlive():
        self.thread.interrupt()
        self.thread.join()

    def bulk_update(self):
        """
        update() should be called when we switch to the search or on the active
        search after we change the current document so that self.changes will
        be taken into consideration
        """

        if not self.changes:
            return

#        # kill the current thread if one is running..
#        if self.thread and self.thread.isAlive():
#            if isinstance(self.thread, UpdateSearchThread):
#                # for now don't interrupt the big threads when we update the
#                # search
#                self.thread.interrupted = True
#            self.thread.join() # wait for the search to end
#
#        # launch a new thread
#        self.thread = SearchThread()
#        self.start(self)

    def incr_update(self):
        if not self.changes:
            return


