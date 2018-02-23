# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
import re
import subprocess
import sys

from os.path import normpath

from .coverage import CoverageData
from .utils import aliases, search_file

output_re = re.compile("[Cc]reating [`'](.*)'$")
source_re = re.compile("[Cc]annot open (source|graph) file")

exclude_line_flag = "_EXCL_"
exclude_line_pattern = re.compile('([GL]COVR?)_EXCL_(LINE|START|STOP)')

c_style_comment_pattern = re.compile('/\*.*?\*/')
cpp_style_comment_pattern = re.compile('//.*?$')


#
# Get the list of datafiles in the directories specified by the user
#
def get_datafiles(flist, options):
    allfiles = set()
    for dir_ in flist:
        if options.gcov_files:
            if options.verbose:
                sys.stdout.write(
                    "Scanning directory %s for gcov files...\n" % (dir_, )
                )
            files = search_file(
                ".*\.gcov$", dir_, exclude_dirs=options.exclude_dirs)
            gcov_files = [file for file in files if file.endswith('gcov')]
            if options.verbose:
                sys.stdout.write(
                    "Found %d files (and will process %d)\n" %
                    (len(files), len(gcov_files))
                )
            allfiles.update(gcov_files)
        else:
            if options.verbose:
                sys.stdout.write(
                    "Scanning directory %s for gcda/gcno files...\n" % (dir_, )
                )
            files = search_file(
                ".*\.gc(da|no)$", dir_, exclude_dirs=options.exclude_dirs)
            # gcno files will *only* produce uncovered results; however,
            # that is useful information for the case where a compilation
            # unit is never actually exercised by the test code.  So, we
            # will process gcno files, but ONLY if there is no corresponding
            # gcda file.
            gcda_files = [
                filenm for filenm in files if filenm.endswith('gcda')
            ]
            tmp = set(gcda_files)
            gcno_files = [
                filenm for filenm in files if
                filenm.endswith('gcno') and filenm[:-2] + 'da' not in tmp
            ]
            if options.verbose:
                sys.stdout.write(
                    "Found %d files (and will process %d)\n" %
                    (len(files), len(gcda_files) + len(gcno_files)))
            allfiles.update(gcda_files)
            allfiles.update(gcno_files)
    return allfiles


noncode_mapper = dict.fromkeys(ord(i) for i in '}{')


def is_non_code(code):
    if sys.version_info < (3, 0):
        code = code.strip().translate(None, '}{')
    else:
        code = code.strip().translate(noncode_mapper)
    return len(code) == 0 or code.startswith("//") or code == 'else'


#
# Process a single gcov datafile
#
def process_gcov_data(data_fname, covdata, source_fname, options):
    logger = Logger(options.verbose)

    INPUT = open(data_fname, "r")

    # Find the source file
    firstline = INPUT.readline()
    fname = guess_source_file_name(
        firstline, data_fname, source_fname,
        root_dir=options.root_dir, starting_dir=options.starting_dir,
        logger=logger)

    logger.verbose_msg("Parsing coverage data for file {}", fname)

    # Return if the filename does not match the filter
    filtered_fname = None
    for i in range(0, len(options.filter)):
        if options.filter[i].match(fname):
            filtered_fname = options.root_filter.sub('', fname)
            break
    if filtered_fname is None:
        logger.verbose_msg("  Filtering coverage data for file {}", fname)
        return

    # Return if the filename matches the exclude pattern
    for exc in options.exclude:
        if (filtered_fname is not None and exc.match(filtered_fname)) or \
                exc.match(fname) or \
                exc.match(os.path.abspath(fname)):
            logger.verbose_msg("  Excluding coverage data for file {}", fname)
            return

    parser = GcovParser(fname, logger=logger)
    for line in INPUT:
        parser.parse_line(line, options.exclude_unreachable_branches)
    parser.update_coverage(covdata)
    parser.check_unclosed_exclusions()

    INPUT.close()


def guess_source_file_name(
        line, data_fname, source_fname, root_dir, starting_dir, logger):
    segments = line.split(':', 3)
    if len(segments) != 4 or not \
            segments[2].lower().strip().endswith('source'):
        raise RuntimeError(
            'Fatal error parsing gcov file, line 1: \n\t"%s"' % line.rstrip()
        )

    gcovname = segments[-1].strip()
    currdir = os.getcwd()
    if source_fname is None:
        fname = guess_source_file_name_via_aliases(
            gcovname, currdir, data_fname)
    else:
        fname = guess_source_file_name_heuristics(
            gcovname, currdir, root_dir, starting_dir, source_fname)

    logger.verbose_msg(
        "Finding source file corresponding to a gcov data file\n"
        '  currdir      {currdir}\n'
        '  gcov_fname   {data_fname}\n'
        '               {segments}\n'
        '  source_fname {source_fname}\n'
        '  root         {root_dir}\n'
        # '  common_dir   {common_dir}\n'
        # '  subdir       {subdir}\n'
        '  fname        {fname}',
        currdir=currdir, data_fname=data_fname, segments=segments,
        source_fname=source_fname, root_dir=root_dir,
        # common_dir=common_dir, subdir=subdir,
        fname=fname)

    return fname


def guess_source_file_name_via_aliases(gcovname, currdir, data_fname):
    common_dir = os.path.commonprefix([data_fname, currdir])
    fname = aliases.unalias_path(os.path.join(common_dir, gcovname))
    if os.path.exists(fname):
        return fname

    initial_fname = fname

    data_fname_dir = os.path.dirname(data_fname)
    fname = aliases.unalias_path(os.path.join(data_fname_dir, gcovname))
    if os.path.exists(fname):
        return fname

    # @latk-2018: The original code is *very* insistent
    # on returning the inital guess. Why?
    return initial_fname


def guess_source_file_name_heuristics(
        gcovname, currdir, root_dir, starting_dir, source_fname):

    # gcov writes filenames with '/' path seperators even if the OS
    # separator is different, so we replace it with the correct separator
    gcovname = gcovname.replace('/', os.sep)

    # 0. Try using the current working directory as the source directory
    fname = os.path.join(currdir, gcovname)
    if os.path.exists(fname):
        return fname

    # 1. Try using the path to common prefix with the root_dir as the source directory
    fname = os.path.join(root_dir, gcovname)
    if os.path.exists(fname):
        return fname

    # 2. Try using the starting directory as the source directory
    fname = os.path.join(starting_dir, gcovname)
    if os.path.exists(fname):
        return fname

    # 3. Try using the path to the gcda file as the source directory
    source_fname_dir = os.path.dirname(source_fname)
    fname = os.path.join(source_fname_dir, os.path.basename(gcovname))
    return fname


class GcovParser(object):
    def __init__(self, fname, logger):
        self.logger = logger
        self.excluding = []
        self.noncode = set()
        self.uncovered = set()
        self.uncovered_exceptional = set()
        self.covered = dict()
        self.branches = dict()
        # self.first_record = True
        self.fname = fname
        self.lineno = 0
        self.last_code_line = ""
        self.last_code_lineno = 0
        self.last_code_line_excluded = False

    def parse_line(self, line, exclude_unreachable_branches):
        # If this is a tag line, we stay on the same line number
        # and can return immediately after processing it.
        # A tag line cannot hold exclusion markers.
        if self.parse_tag_line(line, exclude_unreachable_branches):
            return

        # If this isn't a tag line, this is metadata or source code.
        # e.g.  "  -:  0:Data:foo.gcda" (metadata)
        # or    "  3:  7:  c += 1"      (source code)

        segments = line.split(":", 2)
        # print "\t","Y", segments
        if len(segments) > 1:
            try:
                self.lineno = int(segments[1].strip())
            except ValueError:
                pass  # keep previous line number!

        if exclude_line_flag in line:
            excl_line = False
            for header, flag in exclude_line_pattern.findall(line):
                if self.parse_exclusion_marker(header, flag):
                    excl_line = True

            # We buffer the line exclusion so that it is always
            # the last thing added to the exclusion list (and so
            # only ONE is ever added to the list).  This guards
            # against cases where puts a _LINE and _START (or
            # _STOP) on the same line... it also guards against
            # duplicate _LINE flags.
            if excl_line:
                self.excluding.append(False)

        status = segments[0].strip()
        code = segments[2] if 2 < len(segments) else ""
        is_code_statement = self.parse_code_line(status, code)

        if not is_code_statement:
            self.logger.verbose_msg(
                "Unrecognized GCOV output: {line}\n"
                "\tThis is indicitive of a gcov output parse error.\n"
                "\tPlease report this to the gcovr developers.",
                line=line)

        # save the code line to use it later with branches
        if is_code_statement:
            self.last_code_line = "".join(segments[2:])
            self.last_code_lineno = self.lineno
            self.last_code_line_excluded = bool(self.excluding)

        # clear the excluding flag for single-line excludes
        if self.excluding and not self.excluding[-1]:
            self.excluding.pop()

    def parse_code_line(self, status, code):
        firstchar = status[0]

        if firstchar == '-' or (self.excluding and firstchar in "#=0123456789"):
            # remember certain non-executed lines
            if self.excluding or is_non_code(code):
                self.noncode.add(self.lineno)
            return True

        if firstchar == '#':
            if is_non_code(code):
                self.noncode.add(self.lineno)
            else:
                self.uncovered.add(self.lineno)
            return True

        if firstchar == '=':
            self.uncovered_exceptional.add(self.lineno)
            return True

        if firstchar in "0123456789":
            self.covered[self.lineno] = int(status)
            return True

        return False

    def parse_tag_line(self, line, exclude_unreachable_branches):
        if line.startswith('function '):
            return True

        if line.startswith('call '):
            return True

        if line.startswith('branch '):
            exclude_branch = False
            if exclude_unreachable_branches and \
                    self.lineno == self.last_code_lineno:
                if self.last_code_line_excluded:
                    exclude_branch = True
                    exclude_reason = "marked with exclude pattern"
                else:
                    code = self.last_code_line
                    code = re.sub(cpp_style_comment_pattern, '', code)
                    code = re.sub(c_style_comment_pattern, '', code)
                    code = code.strip()
                    code_nospace = code.replace(' ', '')
                    exclude_branch = \
                        code in ['', '{', '}'] or code_nospace == '{}'
                    exclude_reason = "detected as compiler-generated code"

            if exclude_branch:
                self.logger.verbose_msg(
                    "Excluding unreachable branch on line {line} "
                    "in file {fname}: {reason}",
                    line=self.lineno, fname=self.fname,
                    reason=exclude_reason)
                return True

            fields = line.split()  # e.g. "branch  0 taken 0% (fallthrough)"
            branch_index = int(fields[1])
            try:
                count = int(fields[3])
            except (ValueError, IndexError):
                count = 0
            self.branches.setdefault(self.lineno, {})[branch_index] = count
            return True

        return False

    def parse_exclusion_marker(self, header, flag):
        """Process the exclusion marker

        - START markers are added to the exclusion_stack
        - STOP markers remove a marker from the exclusion_stack
        - LINE markers return True

        returns: True when this line should be excluded, False for n/a.

        header: exclusion marker name, e.g. "LCOV" or "GCOVR"
        flag: exclusion marker action, one of "START", "STOP", or "LINE"
        """
        if flag == 'START':
            self.excluding.append((header, self.lineno))
            return False

        if flag == 'STOP':
            if not self.excluding:
                self.logger.warn(
                    "mismatched coverage exclusion flags.\n"
                    "\t{header}_EXCL_STOP found on line {lineno} "
                    "without corresponding {header}_EXCL_START, "
                    "when processing {fname}",
                    header=header, lineno=self.lineno, fname=self.fname)
                return False

            start_header, start_line = self.excluding.pop()
            if header != start_header:
                self.logger.warn(
                    "{start_header}_EXCL_START found on line {start_line} "
                    "was terminated by {header}_EXCL_STOP "
                    "on line {lineno}, when processing {fname}",
                    start_header=start_header, start_line=start_line,
                    header=header, lineno=self.lineno, fname=self.fname)
            return False

        if flag == 'LINE':
            return True

        assert False, "unknown exclusion marker"  # pragma: no cover

    def check_unclosed_exclusions(self):
        for header, line in self.excluding:
            self.logger.warn(
                "The coverage exclusion region start flag {header}_EXCL_START\n"
                "\ton line {line} did not have corresponding {header}_EXCL_STOP flag\n"
                "\tin file {fname}.",
                header=header, line=line, fname=self.fname)

    def update_coverage(self, covdata):
        self.logger.verbose_msg(
            "uncovered: {parser.uncovered}\n"
            "covered:   {parser.covered}\n"
            "branches:  {parser.branches}\n"
            "noncode:   {parser.noncode}",
            parser=self)

        # If the file is already in covdata, then we
        # remove lines that are covered here.  Otherwise,
        # initialize covdata
        if self.fname not in covdata:
            covdata[self.fname] = CoverageData(
                self.fname, self.uncovered, self.uncovered_exceptional, self.covered, self.branches, self.noncode
            )
        else:
            covdata[self.fname].update(
                uncovered=self.uncovered,
                uncovered_exceptional=self.uncovered_exceptional,
                covered=self.covered,
                branches=self.branches,
                noncode=self.noncode)


class Logger(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def warn(self, pattern, *args, **kwargs):
        """Write a formatted warning to STDERR.

        pattern: a str.format pattern
        args, kwargs: str.format arguments
        """
        pattern = "(WARNING) " + pattern + "\n"
        sys.stderr.write(pattern.format(*args, **kwargs))

    def msg(self, pattern, *args, **kwargs):
        """Write a formatted message to STDOUT.

        pattern: a str.format pattern
        args, kwargs: str.format arguments
        """
        pattern = pattern + "\n"
        sys.stdout.write(pattern.format(*args, **kwargs))

    def verbose_msg(self, pattern, *args, **kwargs):
        """Write a formatted message to STDOUT if in verbose mode.

        see: self.msg()
        """
        if self.verbose:
            self.msg(pattern, *args, **kwargs)


#
# Process a datafile (generated by running the instrumented application)
# and run gcov with the corresponding arguments
#
# This is trickier than it sounds: The gcda/gcno files are stored in the
# same directory as the object files; however, gcov must be run from the
# same directory where gcc/g++ was run.  Normally, the user would know
# where gcc/g++ was invoked from and could tell gcov the path to the
# object (and gcda) files with the --object-directory command.
# Unfortunately, we do everything backwards: gcovr looks for the gcda
# files and then has to infer the original gcc working directory.
#
# In general, (but not always) we can assume that the gcda file is in a
# subdirectory of the original gcc working directory, so we will first
# try ".", and on error, move up the directory tree looking for the
# correct working directory (letting gcov's own error codes dictate when
# we hit the right directory).  This covers 90+% of the "normal" cases.
# The exception to this is if gcc was invoked with "-o ../[...]" (i.e.,
# the object directory was a peer (not a parent/child) of the cwd.  In
# this case, things are really tough.  We accept an argument
# (--object-directory) that SHOULD BE THE SAME as the one povided to
# gcc.  We will then walk that path (backwards) in the hopes of
# identifying the original gcc working directory (there is a bit of
# trial-and-error here)
#
def process_datafile(filename, covdata, options):
    if options.verbose:
        print("Processing file: " + filename)
    #
    # Launch gcov
    #
    abs_filename = os.path.abspath(filename)
    dirname, fname = os.path.split(abs_filename)

    potential_wd = []
    errors = []
    Done = False

    if options.objdir:
        # print "X - objdir"
        src_components = abs_filename.split(os.sep)
        components = normpath(options.objdir).split(os.sep)
        idx = 1
        while idx <= len(components):
            if idx > len(src_components):
                break
            if components[-1 * idx] != src_components[-1 * idx]:
                break
            idx += 1
        if idx > len(components):
            pass  # a parent dir; the normal process will find it
        elif components[-1 * idx] == '..':
            # NB: os.path.join does not re-add leading '/' characters!?!
            dirs = [
                os.path.sep.join(src_components[:len(src_components) - idx])
            ]
            while idx <= len(components) and components[-1 * idx] == '..':
                tmp = []
                for d in dirs:
                    for f in os.listdir(d):
                        x = os.path.join(d, f)
                        if os.path.isdir(x):
                            tmp.append(x)
                dirs = tmp
                idx += 1
            potential_wd = dirs
        else:
            if components[0] == '':
                # absolute path
                tmp = [options.objdir]
            else:
                # relative path: check relative to both the cwd and the
                # gcda file
                tmp = [
                    os.path.join(x, options.objdir) for x in
                    [os.path.dirname(abs_filename), os.getcwd()]
                ]
            potential_wd = [
                testdir for testdir in tmp if os.path.isdir(testdir)
            ]
            if len(potential_wd) == 0:
                errors.append("ERROR: cannot identify the location where GCC "
                              "was run using --object-directory=%s\n" %
                              options.objdir)

    # no objdir was specified (or it was a parent dir); walk up the dir tree
    if len(potential_wd) == 0:
        potential_wd.append(options.root_dir)
        # print "X - potential_wd", options.root_dir
        wd = os.path.split(abs_filename)[0]
        while True:
            potential_wd.append(wd)
            wd = os.path.split(wd)[0]
            if wd == potential_wd[-1]:
                #
                # Stop at the root of the file system
                #
                break
    else:
        # Always add the root directory
        potential_wd.append(options.root_dir)

    #
    # If the first element of cmd - the executable name - has embedded spaces
    # it probably includes extra arguments.
    #
    cmd = options.gcov_cmd.split(' ') + [
        abs_filename,
        "--branch-counts", "--branch-probabilities", "--preserve-paths",
        '--object-directory', dirname
    ]

    # NB: Currently, we will only parse English output
    env = dict(os.environ)
    env['LC_ALL'] = 'en_US'

    while len(potential_wd) > 0 and not Done:
        # NB: either len(potential_wd) == 1, or all entires are absolute
        # paths, so we don't have to chdir(starting_dir) at every
        # iteration.

        #
        # Iterate from the end of the potential_wd list, which is the root
        # directory
        #
        dir_ = potential_wd.pop(0)
        # print "X DIR:", dir_
        os.chdir(dir_)

        if options.verbose:
            sys.stdout.write(
                "Running gcov: '%s' in '%s'\n" % (' '.join(cmd), os.getcwd())
            )
        out, err = subprocess.Popen(
            cmd, env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate()
        out = out.decode('utf-8')
        err = err.decode('utf-8')

        # find the files that gcov created
        gcov_files = {'active': [], 'filter': [], 'exclude': []}
        for line in out.splitlines():
            found = output_re.search(line.strip())
            if found is not None:
                fname = found.group(1)
                if not options.gcov_filter.match(fname):
                    if options.verbose:
                        sys.stdout.write("Filtering gcov file %s\n" % fname)
                    gcov_files['filter'].append(fname)
                    continue
                exclude = False
                for exc in options.gcov_exclude:
                    if exc.match(options.gcov_filter.sub('', fname)) or \
                            exc.match(fname) or \
                            exc.match(os.path.abspath(fname)):
                        exclude = True
                        break
                if not exclude:
                    gcov_files['active'].append(fname)
                elif options.verbose:
                    sys.stdout.write("Excluding gcov file %s\n" % fname)
                    gcov_files['exclude'].append(fname)

        # print "HERE", err, "XXX", source_re.search(err)
        if source_re.search(err):
            #
            # gcov tossed errors: try the next potential_wd
            #
            errors.append(err)
        else:
            #
            # Process *.gcov files
            #
            for fname in gcov_files['active']:
                process_gcov_data(fname, covdata, abs_filename, options)
            Done = True

        if not options.keep:
            for group in gcov_files.values():
                for fname in group:
                    if os.path.exists(fname):
                        # Only remove files that actually exist.
                        os.remove(fname)

    os.chdir(options.root_dir)
    if options.delete:
        if not abs_filename.endswith('gcno'):
            os.remove(abs_filename)

    if not Done:
        sys.stderr.write(
            "(WARNING) GCOV produced the following errors processing %s:\n"
            "\t   %s"
            "\t(gcovr could not infer a working directory that resolved it.)\n"
            % (filename, "\t   ".join(errors))
        )


#
#  Process Already existing gcov files
#
def process_existing_gcov_file(filename, covdata, options):
    #
    # Ignore this file if it does not match the gcov filter
    #
    if not options.gcov_filter.match(filename):
        if options.verbose:
            sys.stdout.write("This gcov file does not match the filter: %s\n" % filename)
        return
    #
    # Ignore this file if it matches one of the exclusion regex's
    #
    for exc in options.gcov_exclude:
        if exc.match(options.gcov_filter.sub('', filename)) or \
                exc.match(filename) or \
                exc.match(os.path.abspath(filename)):
            if options.verbose:
                sys.stdout.write("Excluding gcov file: %s\n" % filename)
            return
    #
    # Process the gcov data file
    #
    process_gcov_data(filename, covdata, None, options)
    #
    # Remove the file unless the user has indicated that we keep gcov data files
    #
    if not options.keep:
        #
        # Only remove files that actually exist.
        #
        if os.path.exists(filename):
            os.remove(filename)
