# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import os
import re
import shlex
import subprocess
import sys
import io

from .utils import search_file, Logger, commonpath
from .workers import locked_directory
from .coverage import FileCoverage

output_re = re.compile(r"[Cc]reating [`'](.*)'$")
source_re = re.compile(r"[Cc](annot|ould not) open (source|graph|output) file")

exclude_line_flag = "_EXCL_"
exclude_line_pattern = re.compile(r'([GL]COVR?)_EXCL_(START|STOP)')

c_style_comment_pattern = re.compile(r'/\*.*?\*/')
cpp_style_comment_pattern = re.compile(r'//.*?$')


def find_existing_gcov_files(search_path, logger, exclude_dirs):
    """Find .gcov files under the given search path.
    """
    logger.verbose_msg(
        "Scanning directory {} for gcov files...", search_path)
    gcov_files = list(search_file(
        re.compile(r".*\.gcov$").match, search_path,
        exclude_dirs=exclude_dirs))
    logger.verbose_msg(
        "Found {} files (and will process all of them)",
        len(gcov_files))
    return gcov_files


def find_datafiles(search_path, logger, exclude_dirs):
    """Find .gcda and .gcno files under the given search path.

    The .gcno files will *only* produce uncovered results.
    However, that is useful information when a compilation unit
    is never actually exercised by the test code.
    So we ONLY return them if there's no corresponding .gcda file.
    """
    logger.verbose_msg(
        "Scanning directory {} for gcda/gcno files...", search_path)
    files = list(search_file(
        re.compile(r".*\.gc(da|no)$").match, search_path,
        exclude_dirs=exclude_dirs))
    gcda_files = []
    gcno_files = []
    known_file_stems = set()
    for filename in files:
        stem, ext = os.path.splitext(filename)
        if ext == '.gcda':
            gcda_files.append(filename)
            known_file_stems.add(stem)
        elif ext == '.gcno':
            gcno_files.append(filename)
    # remove gcno files that match a gcno stem
    gcno_files = [
        filename
        for filename in gcno_files
        if os.path.splitext(filename)[0] not in known_file_stems
    ]
    logger.verbose_msg(
        "Found {} files (and will process {})",
        len(files), len(gcda_files) + len(gcno_files))
    return gcda_files + gcno_files


noncode_mapper = dict.fromkeys(ord(i) for i in '}{')


def is_non_code(code):
    code = code.strip().translate(noncode_mapper)
    return len(code) == 0 or code.startswith("//") or code == 'else'


#
# Process a single gcov datafile
#
def process_gcov_data(data_fname, covdata, source_fname, options, currdir=None):
    logger = Logger(options.verbose)
    with io.open(data_fname, "r", encoding=options.source_encoding,
                 errors='replace') as INPUT:

        # Find the source file
        firstline = INPUT.readline()
        fname = guess_source_file_name(
            firstline, data_fname, source_fname,
            root_dir=options.root_dir, starting_dir=options.starting_dir,
            obj_dir=None if options.objdir is None else os.path.abspath(options.objdir),
            logger=logger, currdir=currdir)

        logger.verbose_msg("Parsing coverage data for file {}", fname)

        # Return if the filename does not match the filter
        # Return if the filename matches the exclude pattern
        filtered, excluded = apply_filter_include_exclude(
            fname, options.filter, options.exclude)

        if filtered:
            logger.verbose_msg("  Filtering coverage data for file {}", fname)
            return

        if excluded:
            logger.verbose_msg("  Excluding coverage data for file {}", fname)
            return

        key = os.path.normpath(fname)

        parser = GcovParser(key, logger=logger)
        parser.parse_all_lines(
            INPUT,
            exclude_unreachable_branches=options.exclude_unreachable_branches,
            exclude_throw_branches=options.exclude_throw_branches,
            ignore_parse_errors=options.gcov_ignore_parse_errors,
            exclude_lines_by_pattern=options.exclude_lines_by_pattern,
            exclude_function_lines=options.exclude_function_lines)

        covdata.setdefault(key, FileCoverage(key)).update(parser.coverage)


def guess_source_file_name(
        line, data_fname, source_fname, root_dir, starting_dir, obj_dir, logger, currdir=None):
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
            gcovname, currdir, root_dir, starting_dir, obj_dir, source_fname)

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
    common_dir = commonpath([data_fname, currdir])
    fname = os.path.realpath(os.path.join(common_dir, gcovname))
    if os.path.exists(fname):
        return fname

    initial_fname = fname

    data_fname_dir = os.path.dirname(data_fname)
    fname = os.path.realpath(os.path.join(data_fname_dir, gcovname))
    if os.path.exists(fname):
        return fname

    # @latk-2018: The original code is *very* insistent
    # on returning the inital guess. Why?
    return initial_fname


def guess_source_file_name_heuristics(
        gcovname, currdir, root_dir, starting_dir, obj_dir, source_fname):

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

    # 3. Try using relative path from object dir
    if obj_dir is not None:
        fname = os.path.normpath(os.path.join(obj_dir, gcovname))
        if os.path.exists(fname):
            return fname

    # Get path of gcda file
    source_fname_dir = os.path.dirname(source_fname)

    # 4. Try using the path to the gcda as the source directory
    fname = os.path.join(source_fname_dir, gcovname)
    if os.path.exists(fname):
        return os.path.normpath(fname)

    # 5. Try using the path to the gcda file as the source directory, removing the path part from the gcov file
    fname = os.path.join(source_fname_dir, os.path.basename(gcovname))
    return fname


class GcovParser(object):
    def __init__(self, fname, logger):
        self.logger = logger
        self.excluding = []
        self.coverage = FileCoverage(fname)
        # self.first_record = True
        self.fname = fname
        self.lineno = 0
        self.last_code_line = ""
        self.last_code_lineno = 0
        self.last_code_line_excluded = False
        self.unrecognized_lines = []
        self.deferred_exceptions = []
        self.last_was_specialization_section_marker = False
        self.last_was_function_marker = False

    def parse_all_lines(
        self, lines, exclude_unreachable_branches, exclude_throw_branches,
        ignore_parse_errors, exclude_lines_by_pattern, exclude_function_lines
    ):
        exclude_lines_by_pattern_regex = (re.compile(exclude_lines_by_pattern)
                                          if exclude_lines_by_pattern
                                          else None)
        for line in lines:
            try:
                self.parse_line(
                    line, exclude_unreachable_branches, exclude_throw_branches,
                    exclude_lines_by_pattern_regex, exclude_function_lines)
            except Exception as ex:
                self.unrecognized_lines.append(line)
                self.deferred_exceptions.append(ex)

        self.check_unclosed_exclusions()
        self.check_unrecognized_lines(ignore_parse_errors=ignore_parse_errors)

    def parse_line(
        self, line, exclude_unreachable_branches, exclude_throw_branches,
        exclude_lines_by_pattern_regex, exclude_function_lines
    ):
        # If this is a tag line, we stay on the same line number
        # and can return immediately after processing it.
        # A tag line cannot hold exclusion markers.
        if self.parse_tag_line(
            line, exclude_unreachable_branches, exclude_throw_branches
        ):
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

        status = segments[0].strip()
        code = segments[2] if 2 < len(segments) else ""

        if exclude_line_flag in line:
            for header, flag in exclude_line_pattern.findall(line):
                self.parse_exclusion_marker(header, flag)
        if exclude_lines_by_pattern_regex:
            if exclude_lines_by_pattern_regex.match(code):
                self.excluding.append(False)

        is_code_statement = self.parse_code_line(status, code, exclude_function_lines)

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

    def parse_code_line(self, status, code, exclude_function_lines):
        firstchar = status[0]

        last_was_function_marker = self.last_was_function_marker
        self.last_was_function_marker = False

        noncode = False
        count = None

        if firstchar == '-' or (self.excluding and firstchar in "#=0123456789"):
            # remember certain non-executed lines
            if self.excluding or is_non_code(code):
                noncode = True
        # "#": uncovered
        # "=": uncovered, but only reachable through exceptions
        elif firstchar in "#=":
            if self.excluding or is_non_code(code):
                noncode = True
            else:
                count = 0
        elif firstchar in "0123456789":
            # GCOV 8 marks partial coverage
            # with a trailing "*" after the execution count.
            count = int(status.rstrip('*'))
        else:
            return False

        if exclude_function_lines and last_was_function_marker:
            noncode = True

        if noncode:
            self.coverage.line(self.lineno).noncode = True
        elif count is not None:
            # self.coverage.line(self.lineno)  # sets count to 0 if not present before
            self.coverage.line(self.lineno).count += count

        return True

    def parse_tag_line(
        self, line, exclude_unreachable_branches, exclude_throw_branches
    ):
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
            self.last_was_function_marker = True
            return True

        if line.startswith('call '):
            return True

        if line.startswith('branch '):

            exclude_reason = None

            if self.lineno != self.last_code_lineno:
                # apply no exclusions if this doesn't look like a code line.
                pass

            elif self.last_code_line_excluded:
                exclude_reason = "marked with exclude pattern"

            elif exclude_unreachable_branches:
                code = self.last_code_line
                code = re.sub(cpp_style_comment_pattern, '', code)
                code = re.sub(c_style_comment_pattern, '', code)
                code = code.strip()
                code_nospace = code.replace(' ', '')
                if code_nospace in ['', '{', '}', '{}']:
                    exclude_reason = "detected as compiler-generated code"

            if exclude_reason is not None:
                self.logger.verbose_msg(
                    "Excluding unreachable branch on line {line} "
                    "in file {fname}: {reason}",
                    line=self.lineno, fname=self.fname,
                    reason=exclude_reason)
                return True

            # branch tags can look like:
            #   branch  1 never executed
            #   branch  2 taken 12%
            #   branch  3 taken 12% (fallthrough)
            #   branch  3 taken 12% (throw)
            # where the percentage should usually be a count.

            fields = line.split()  # e.g. "branch  0 taken 0% (fallthrough)"
            assert len(fields) >= 4, \
                "Unclear branch tag format: {}".format(line)

            branch_index = int(fields[1])

            if fields[2:] == ['never', 'executed']:
                count = 0

            elif fields[3].endswith('%'):
                percentage = int(fields[3][:-1])
                # can't really convert percentage to count,
                # so normalize to zero/one
                count = 1 if percentage > 0 else 0

            else:
                count = int(fields[3])

            is_fallthrough = fields[-1] == '(fallthrough)'
            is_throw = fields[-1] == '(throw)'

            if exclude_throw_branches and is_throw:
                return True

            branch_cov = self.coverage.line(self.lineno).branch(branch_index)
            branch_cov.count += count
            if is_fallthrough:
                branch_cov.fallthrough = True
            if is_throw:
                branch_cov.throw = True

            return True

        return False

    def parse_exclusion_marker(self, header, flag):
        """Process the exclusion marker

        - START markers are added to the exclusion_stack
        - STOP markers remove a marker from the exclusion_stack

        header: exclusion marker name, e.g. "LCOV" or "GCOVR"
        flag: exclusion marker action, one of "START", "STOP"
        """
        if flag == 'START':
            self.excluding.append((header, self.lineno))
            return

        if flag == 'STOP':
            if not self.excluding:
                self.logger.warn(
                    "mismatched coverage exclusion flags.\n"
                    "\t{header}_EXCL_STOP found on line {lineno} "
                    "without corresponding {header}_EXCL_START, "
                    "when processing {fname}",
                    header=header, lineno=self.lineno, fname=self.fname)
                return

            start_header, start_line = self.excluding.pop()
            if header != start_header:
                self.logger.warn(
                    "{start_header}_EXCL_START found on line {start_line} "
                    "was terminated by {header}_EXCL_STOP "
                    "on line {lineno}, when processing {fname}",
                    start_header=start_header, start_line=start_line,
                    header=header, lineno=self.lineno, fname=self.fname)
            return

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


def process_datafile(filename, covdata, options, toerase, workdir):
    r"""Run gcovr in a suitable directory to collect coverage from gcda files.

    Params:
        filename (path): the path to a gcda or gcno file
        covdata (dict, mutable): the global covdata dictionary
        options (object): the configuration options namespace
        toerase (set, mutable): files that should be deleted later
        workdir (path or None): the per-thread work directory

    Returns:
        Nothing.

    Finding a suitable working directory is tricky.
    The coverage files (gcda and gcno) are stored next to object (.o) files.
    However, gcov needs to also resolve the source file name.
    The relative source file paths in the coverage data
    are relative to the gcc working directory.
    Therefore, gcov must be invoked in the same directory as gcc.
    How to find that directory? By various heuristics.

    This is complicated by the problem that the build process tells gcc
    where to run, where the sources are, and where to put the object files.
    We only know the object files and have to work everything out in reverse.

    If present, the *workdir* argument is always tried first.

    Ideally, the build process only runs gcc from *one* directory
    and the user can provide this directory as the ``--object-directory``.
    If it exists, we try that path as a workdir,
    If the path is relative,
    it is resolved relative to the gcovr cwd and the object file location.

    We next try the ``--root`` directory.
    TODO: should probably also be the gcovr start directory.

    If none of those work, we assume that
    the object files are in a subdirectory of the gcc working directory,
    i.e. we can walk the directory tree upwards.

    All of this works fine unless gcc was invoked like ``gcc -o ../path``,
    i.e. the object files are in a sibling directory.
    TODO: So far there is no good way to address this case.
    """
    logger = Logger(options.verbose)

    logger.verbose_msg("Processing file: {}", filename)

    abs_filename = os.path.abspath(filename)

    errors = []

    potential_wd = []

    if options.objdir:
        potential_wd = find_potential_working_directories_via_objdir(
            abs_filename, options.objdir, error=errors.append)

    # no objdir was specified or objdir didn't exist
    consider_parent_directories = not potential_wd

    # Always add the root directory
    potential_wd.append(options.root_dir)

    if consider_parent_directories:
        wd = os.path.dirname(abs_filename)
        while wd != potential_wd[-1]:
            potential_wd.append(wd)
            wd = os.path.dirname(wd)

    # Ensure the working directory for this thread is first (if any)
    if workdir is not None:
        potential_wd = [workdir] + potential_wd

    for wd in potential_wd:
        done = run_gcov_and_process_files(
            abs_filename, covdata,
            options=options, logger=logger, toerase=toerase,
            error=errors.append, chdir=wd, tempdir=workdir)

        if options.delete:
            if not abs_filename.endswith('gcno'):
                toerase.add(abs_filename)

        if done:
            return

    logger.warn(
        "GCOV produced the following errors processing {filename}:\n"
        "\t{errors}\n"
        "\t(gcovr could not infer a working directory that resolved it.)",
        filename=filename, errors="\n\t".join(errors))


def find_potential_working_directories_via_objdir(abs_filename, objdir, error):
    # absolute path - just return the objdir
    if os.path.isabs(objdir):
        if os.path.isdir(objdir):
            return [objdir]

    # relative path: check relative to both the cwd and the gcda file
    else:
        potential_wd = [
            testdir
            for prefix in [os.path.dirname(abs_filename), os.getcwd()]
            for testdir in [os.path.join(prefix, objdir)]
            if os.path.isdir(testdir)
        ]

        if potential_wd:
            return potential_wd

    error("ERROR: cannot identify the location where GCC "
          "was run using --object-directory=%s\n" % objdir)

    return []


def run_gcov_and_process_files(
        abs_filename, covdata, options, logger, error, toerase, chdir, tempdir):
    # If the first element of cmd - the executable name - has embedded spaces
    # (other than within quotes), it probably includes extra arguments.
    cmd = shlex.split(options.gcov_cmd) + [
        abs_filename,
        "--branch-counts", "--branch-probabilities", "--preserve-paths",
        '--object-directory', os.path.dirname(abs_filename),
    ]

    # NB: Currently, we will only parse English output
    env = dict(os.environ)
    env['LC_ALL'] = 'en_US'
    env['LANGUAGE'] = 'en_US'

    logger.verbose_msg(
        "Running gcov: '{cmd}' in '{cwd}'",
        cmd=' '.join(cmd),
        cwd=chdir)

    with locked_directory(chdir):
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
        error(err)
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
            logger.verbose_msg("Filtering gcov file {}", fname)
            continue

        if excluded:
            logger.verbose_msg("Excluding gcov file {}", fname)
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
            "This gcov file does not match the filter: {}", filename)
        return

    if excluded:
        logger.verbose_msg("Excluding gcov file: {}", filename)
        return

    process_gcov_data(filename, covdata, None, options)

    if not options.keep:
        toerase.add(filename)


def apply_filter_include_exclude(
        filename, include_filters, exclude_filters):
    """Apply inclusion/exclusion filters to filename

    The include_filters are tested against
    the given (relative) filename.
    The exclude_filters are tested against
    the stripped, given (relative), and absolute filenames.

    filename (str): the file path to match, should be relative
    include_filters (list of regex): ANY of these filters must match
    exclude_filters (list of regex): NONE of these filters must match

    returns: (filtered, exclude)
        filtered (bool): True when filename failed the include_filter
        excluded (bool): True when filename failed the exclude_filters
    """

    filtered = not any(f.match(filename) for f in include_filters)
    excluded = False

    if filtered:
        return filtered, excluded

    excluded = any(f.match(filename) for f in exclude_filters)

    return filtered, excluded
