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

from .utils import aliases, search_file, Logger
from .workers import locked_directory
from .coverage import CoverageData

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
    logger = Logger(options.verbose)

    allfiles = set()
    for dir_ in flist:
        if options.gcov_files:
            logger.verbose_msg(
                "Scanning directory {0} for gcov files...", dir_)
            files = search_file(
                ".*\.gcov$", dir_, exclude_dirs=options.exclude_dirs)
            gcov_files = [file for file in files if file.endswith('gcov')]
            logger.verbose_msg(
                "Found {0} files (and will process {1})",
                len(files), len(gcov_files))
            allfiles.update(gcov_files)
        else:
            logger.verbose_msg(
                "Scanning directory {0} for gcda/gcno files...", dir_)
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
            logger.verbose_msg(
                "Found {0} files (and will process {1})",
                len(files), len(gcda_files) + len(gcno_files))
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
def process_gcov_data(data_fname, covdata, source_fname, options, currdir=None):
    logger = Logger(options.verbose)
    INPUT = open(data_fname, "r")

    # Find the source file
    firstline = INPUT.readline()
    fname = guess_source_file_name(
        firstline, data_fname, source_fname,
        root_dir=options.root_dir, starting_dir=options.starting_dir,
        logger=logger, currdir=currdir)

    logger.verbose_msg("Parsing coverage data for file {0}", fname)

    # Return if the filename does not match the filter
    # Return if the filename matches the exclude pattern
    filtered, excluded = apply_filter_include_exclude(
        fname, options.filter, options.exclude, strip=options.root_filter)

    if filtered:
        logger.verbose_msg("  Filtering coverage data for file {0}", fname)
        return

    if excluded:
        logger.verbose_msg("  Excluding coverage data for file {0}", fname)
        return

    parser = GcovParser(fname, logger=logger)
    parser.parse_all_lines(
        INPUT,
        exclude_unreachable_branches=options.exclude_unreachable_branches,
        ignore_parse_errors=options.gcov_ignore_parse_errors)
    parser.update_coverage(covdata)

    INPUT.close()


def guess_source_file_name(
        line, data_fname, source_fname, root_dir, starting_dir, logger, currdir=None):
    segments = line.split(':', 3)
    if len(segments) != 4 or not \
            segments[2].lower().strip().endswith('source'):
        raise RuntimeError(
            'Fatal error parsing gcov file %s, line 1: \n\t"%s"' % (data_fname, line.rstrip())
        )
    gcovname = segments[-1].strip()
    if currdir is None:
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
        self.unrecognized_lines = []
        self.deferred_exceptions = []
        self.last_was_specialization_section_marker = False

    def parse_all_lines(self, lines, exclude_unreachable_branches, ignore_parse_errors):
        for line in lines:
            try:
                self.parse_line(line, exclude_unreachable_branches)
            except Exception as ex:
                self.unrecognized_lines.append(line)
                self.deferred_exceptions.append(ex)

        self.check_unclosed_exclusions()
        self.check_unrecognized_lines(ignore_parse_errors=ignore_parse_errors)

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
            self.unrecognized_lines.append(line)

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
            # GCOV 8 marks partial coverage
            # with a trailing "*" after the execution count.
            self.covered[self.lineno] = int(status.rstrip('*'))
            return True

        return False

    def parse_tag_line(self, line, exclude_unreachable_branches):
        # Start or end a template/macro specialization section
        if line.startswith('-----'):
            self.last_was_specialization_section_marker = True
            return True

        last_was_marker = self.last_was_specialization_section_marker
        self.last_was_specialization_section_marker = False

        # A specialization section marker is either followed by a section or
        # ends it. If it starts a section, the next line contains a function
        # name, followed by a colon. A function name cannot be parsed reliably,
        # so we assume it is a function, and try to disprove this assumption by
        # comparing with other kinds of lines.
        if last_was_marker:
            # 1. a function must end with a colon
            is_function = line.endswith(':')

            # 2. a function cannot start with space
            if is_function:
                is_function = not line.startswith(' ')

            # 3. a function cannot start with a tag
            if is_function:
                tags = 'function call branch'.split()
                is_function = not any(
                    line.startswith(tag + ' ') for tag in tags)

            # If this line turned out to be a function, discard it.
            return True

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

    def check_unrecognized_lines(self, ignore_parse_errors):
        if not self.unrecognized_lines:
            return

        self.logger.warn(
            "Unrecognized GCOV output for {source}\n"
            "\t  {lines}\n"
            "\tThis is indicative of a gcov output parse error.\n"
            "\tPlease report this to the gcovr developers\n"
            "\tat <https://github.com/gcovr/gcovr/issues>.",
            source=self.fname,
            lines="\n\t  ".join(self.unrecognized_lines))

        for ex in self.deferred_exceptions:
            self.logger.warn(
                "Exception during parsing:\n"
                "\t{type}: {msg}",
                type=type(ex).__name__, msg=ex)

        if ignore_parse_errors:
            return

        self.logger.error(
            "Exiting because of parse errors.\n"
            "\tYou can run gcovr with --gcov-ignore-parse-errors\n"
            "\tto continue anyway.")

        # if we caught an exception, re-raise it for the traceback
        for ex in self.deferred_exceptions:
            raise ex

        sys.exit(1)

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
            covdata[self.fname] = CoverageData(self.fname)
        covdata[self.fname].update(
            uncovered=self.uncovered,
            uncovered_exceptional=self.uncovered_exceptional,
            covered=self.covered,
            branches=self.branches,
            noncode=self.noncode)


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
def process_datafile(filename, covdata, options, toerase, workdir):
    logger = Logger(options.verbose)

    logger.verbose_msg("Processing file: {0}", filename)

    abs_filename = os.path.abspath(filename)
    dirname, fname = os.path.split(abs_filename)

    errors = []

    potential_wd = find_potential_working_directories_via_objdir(
        abs_filename, options.objdir, errors=errors)

    # no objdir was specified (or it was a parent dir); walk up the dir tree
    if len(potential_wd) == 0:
        potential_wd.append(options.root_dir)
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

    # Ensure the working directory for this thread is first (if any)
    if workdir is not None:
        potential_wd = [workdir] + potential_wd

    # Iterate from the end of the potential_wd list, which is the root
    # directory

    #
    # @latk - 2018: not true, this iterates from the start of the list.
    # Is that a bug?
    done = False
    for dir_ in potential_wd:
        if done:
            break

        # NB: either len(potential_wd) == 1, or all entires are absolute
        # paths, so we don't have to chdir(starting_dir) at every
        # iteration.

        with locked_directory(dir_):
            done = run_gcov_and_process_files(
                abs_filename, dirname, covdata,
                options=options, logger=logger, toerase=toerase, errors=errors, chdir=dir_, tempdir=workdir)

            if options.delete:
                if not abs_filename.endswith('gcno'):
                    toerase.add(abs_filename)

    if not done:
        logger.warn(
            "GCOV produced the following errors processing {filename}:\n"
            "\t{errors}\n"
            "\t(gcovr could not infer a working directory that resolved it.)",
            filename=filename, errors="\n\t".join(errors))


def find_potential_working_directories_via_objdir(abs_filename, objdir, errors):
    if not objdir:
        return []

    src_components = abs_filename.split(os.sep)
    components = normpath(objdir).split(os.sep)

    # find last different component
    idx = 1
    while idx <= len(components) and idx <= len(src_components):
        if components[-idx] != src_components[-idx]:
            break
        idx += 1

    if idx > len(components):
        return []  # a parent dir; the normal process will find it

    if components[-idx] == '..':
        # NB: os.path.join does not re-add leading '/' characters!?!
        dirs = [os.path.sep.join(src_components[:-idx])]
        while idx <= len(components) and components[-idx] == '..':
            dirs = list(expand_subdirectories(*dirs))
            idx += 1
        return dirs

    if components[0] == '':
        # absolute path
        tmp = [objdir]
    else:
        # relative path: check relative to both the cwd and the
        # gcda file
        tmp = [
            os.path.join(x, objdir) for x in
            [os.path.dirname(abs_filename), os.getcwd()]
        ]

    potential_wd = [testdir for testdir in tmp if os.path.isdir(testdir)]

    if len(potential_wd) == 0:
        errors.append("ERROR: cannot identify the location where GCC "
                      "was run using --object-directory=%s\n" %
                      objdir)

    return potential_wd


def expand_subdirectories(*directories):
    for directory in directories:
        for entry in os.listdir(directory):
            subdir = os.path.join(directory, entry)
            if os.path.isdir(subdir):
                yield subdir


def run_gcov_and_process_files(
        abs_filename, dirname, covdata, options, logger, errors, toerase, chdir, tempdir):
    # If the first element of cmd - the executable name - has embedded spaces
    # it probably includes extra arguments.
    cmd = options.gcov_cmd.split(' ') + [
        abs_filename,
        "--branch-counts", "--branch-probabilities", "--preserve-paths",
        '--object-directory', dirname
    ]

    # NB: Currently, we will only parse English output
    env = dict(os.environ)
    env['LC_ALL'] = 'en_US'

    logger.verbose_msg(
        "Running gcov: '{cmd}' in '{cwd}'",
        cmd=' '.join(cmd),
        cwd=chdir)

    out, err = subprocess.Popen(
        cmd, env=env, cwd=chdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')

    # find the files that gcov created
    active_gcov_files, all_gcov_files = select_gcov_files_from_stdout(
        out,
        gcov_filter=options.gcov_filter,
        gcov_exclude=options.gcov_exclude,
        logger=logger,
        chdir=chdir,
        tempdir=tempdir)

    if source_re.search(err):
        # gcov tossed errors: try the next potential_wd
        errors.append(err)
        done = False
    else:
        # Process *.gcov files
        for fname in active_gcov_files:
            process_gcov_data(fname, covdata, abs_filename, options)
        done = True

    if not options.keep:
        toerase.update(all_gcov_files)

    return done


def select_gcov_files_from_stdout(out, gcov_filter, gcov_exclude, logger, chdir, tempdir):
    active_files = []
    all_files = []

    for line in out.splitlines():
        found = output_re.search(line.strip())
        if found is None:
            continue

        fname = found.group(1)
        full = os.path.join(chdir, fname)
        all_files.append(full)

        filtered, excluded = apply_filter_include_exclude(
            fname, gcov_filter, gcov_exclude)

        if filtered:
            logger.verbose_msg("Filtering gcov file {0}", fname)
            continue

        if excluded:
            logger.verbose_msg("Excluding gcov file {0}", fname)
            continue

        if tempdir and tempdir != chdir:
            import shutil
            active_files.append(os.path.join(tempdir, fname))
            shutil.copyfile(full, active_files[-1])
        else:
            active_files.append(full)

    return active_files, all_files


#
#  Process Already existing gcov files
#
def process_existing_gcov_file(filename, covdata, options, toerase, workdir):
    logger = Logger(options.verbose)

    filtered, excluded = apply_filter_include_exclude(
        filename, options.gcov_filter, options.gcov_exclude)

    if filtered:
        logger.verbose_msg(
            "This gcov file does not match the filter: {0}", filename)
        return

    if excluded:
        logger.verbose_msg("Excluding gcov file: {0}", filename)
        return

    process_gcov_data(filename, covdata, None, options)

    if not options.keep:
        toerase.add(filename)


def apply_filter_include_exclude(
        filename, include_filters, exclude_filters, strip=None):
    """Apply inclusion/exclusion filters to filename

    The include_filters are tested against
    the given (relative) filename.
    The exclude_filters are tested against
    the stripped, given (relative), and absolute filenames.

    filename (str): the file path to match, should be relative
    include_filters (list of regex): ANY of these filters must match
    exclude_filters (list of regex): NONE of these filters must match
    strip (optional regex): Strip prefix from filename.
        If None, use matched include filter.

    returns: (filtered, exclude)
        filtered (bool): True when filename failed the include_filter
        excluded (bool): True when filename failed the exclude_filters
    """
    filtered = True
    excluded = False

    filtered_filename = None
    for filter in include_filters:
        if filter.match(filename):
            filtered = False
            if strip is None:
                filtered_filename = filter.sub('', filename)
            else:
                filtered_filename = strip.sub('', filename)
            break

    if filtered:
        return filtered, excluded

    abs_filename = os.path.abspath(filename)

    excluded = any(
        exc.match(f)
        for f in [filtered_filename, filename, abs_filename]
        for exc in exclude_filters)

    return filtered, excluded
