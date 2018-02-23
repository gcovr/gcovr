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
    INPUT = open(data_fname, "r")
    #
    # Get the filename
    #
    line = INPUT.readline()
    segments = line.split(':', 3)
    if len(segments) != 4 or not \
            segments[2].lower().strip().endswith('source'):
        raise RuntimeError(
            'Fatal error parsing gcov file, line 1: \n\t"%s"' % line.rstrip()
        )
    #
    # Find the source file
    #
    currdir = os.getcwd()
    root_dir = options.root_dir
    if source_fname is None:
        common_dir = os.path.commonprefix([data_fname, currdir])
        fname = aliases.unalias_path(os.path.join(common_dir, segments[-1].strip()))
        if not os.path.exists(fname):
            # let's try using the path to the gcov file as base directory
            # Test before assigning not to change behavior compared to previous versions
            possible_gcov_fname = aliases.unalias_path(os.path.join(os.path.dirname(data_fname), segments[-1].strip()))
            if os.path.exists(possible_gcov_fname):
                fname = possible_gcov_fname
    else:
        # gcov writes filenames with '/' path seperators even if the OS
        # separator is different, so we replace it with the correct separator
        gcovname = segments[-1].strip().replace('/', os.sep)

        # 0. Try using the current working directory as the source directory
        fname = os.path.join(currdir, gcovname)
        if not os.path.exists(fname):
            # 1. Try using the path to common prefix with the root_dir as the source directory
            fname = os.path.join(root_dir, gcovname)
            if not os.path.exists(fname):
                # 2. Try using the starting directory as the source directory
                fname = os.path.join(options.starting_dir, gcovname)
                if not os.path.exists(fname):
                    # 3. Try using the path to the gcda file as the source directory
                    fname = os.path.join(os.path.dirname(source_fname), os.path.basename(gcovname))

    if options.verbose:
        print("Finding source file corresponding to a gcov data file")
        print('  currdir      ' + currdir)
        print('  gcov_fname   ' + data_fname)
        print('               ' + str(segments))
        print('  source_fname ' + str(source_fname))
        print('  root         ' + root_dir)
        # print('  common_dir   ' + common_dir)
        # print('  subdir       ' + subdir)
        print('  fname        ' + fname)

    if options.verbose:
        sys.stdout.write("Parsing coverage data for file %s\n" % fname)
    #
    # Return if the filename does not match the filter
    #
    filtered_fname = None
    for i in range(0, len(options.filter)):
        if options.filter[i].match(fname):
            filtered_fname = options.root_filter.sub('', fname)
            break
    if filtered_fname is None:
        if options.verbose:
            sys.stdout.write("  Filtering coverage data for file %s\n" % fname)
        return
    #
    # Return if the filename matches the exclude pattern
    #
    for exc in options.exclude:
        if (filtered_fname is not None and exc.match(filtered_fname)) or \
                exc.match(fname) or \
                exc.match(os.path.abspath(fname)):
            if options.verbose:
                sys.stdout.write(
                    "  Excluding coverage data for file %s\n" % fname
                )
            return
    #
    # Parse each line, and record the lines that are uncovered
    #
    excluding = []
    noncode = set()
    uncovered = set()
    uncovered_exceptional = set()
    covered = {}
    branches = {}
    # first_record=True
    lineno = 0
    last_code_line = ""
    last_code_lineno = 0
    last_code_line_excluded = False
    for line in INPUT:
        segments = line.split(":", 2)
        # print "\t","Y", segments
        tmp = segments[0].strip()
        if len(segments) > 1:
            try:
                lineno = int(segments[1].strip())
            except:  # noqa E722
                pass  # keep previous line number!

        if exclude_line_flag in line:
            excl_line = False
            for header, flag in exclude_line_pattern.findall(line):
                if process_exclusion_marker(header, flag, excluding, lineno=lineno, fname=fname):
                    excl_line = True

            # We buffer the line exclusion so that it is always
            # the last thing added to the exclusion list (and so
            # only ONE is ever added to the list).  This guards
            # against cases where puts a _LINE and _START (or
            # _STOP) on the same line... it also guards against
            # duplicate _LINE flags.
            if excl_line:
                excluding.append(False)

        is_code_statement = False
        if tmp[0] == '-' or (excluding and tmp[0] in "#=0123456789"):
            is_code_statement = True
            code = segments[2].strip()
            # remember certain non-executed lines
            if excluding or is_non_code(segments[2]):
                noncode.add(lineno)
        elif tmp[0] == '#':
            is_code_statement = True
            if is_non_code(segments[2]):
                noncode.add(lineno)
            else:
                uncovered.add(lineno)
        elif tmp[0] == '=':
            is_code_statement = True
            uncovered_exceptional.add(lineno)
        elif tmp[0] in "0123456789":
            is_code_statement = True
            covered[lineno] = int(segments[0].strip())
        elif tmp.startswith('branch'):
            exclude_branch = False
            if options.exclude_unreachable_branches and \
                    lineno == last_code_lineno:
                if last_code_line_excluded:
                    exclude_branch = True
                    exclude_reason = "marked with exclude pattern"
                else:
                    code = last_code_line
                    code = re.sub(cpp_style_comment_pattern, '', code)
                    code = re.sub(c_style_comment_pattern, '', code)
                    code = code.strip()
                    code_nospace = code.replace(' ', '')
                    exclude_branch = \
                        code in ['', '{', '}'] or code_nospace == '{}'
                    exclude_reason = "detected as compiler-generated code"

            if exclude_branch:
                if options.verbose:
                    sys.stdout.write(
                        "Excluding unreachable branch on line %d "
                        "in file %s (%s).\n"
                        % (lineno, fname, exclude_reason)
                    )
            else:
                fields = line.split()
                try:
                    count = int(fields[3])
                except:  # noqa E722
                    count = 0
                branches.setdefault(lineno, {})[int(fields[1])] = count
        elif tmp.startswith('call'):
            pass
        elif tmp.startswith('function'):
            pass
        elif tmp[0] == 'f':
            pass
            # if first_record:
            #     first_record=False
            #     uncovered.add(prev)
            # if prev in uncovered:
            #     tokens=re.split('[ \t]+',tmp)
            #     if tokens[3] != "0":
            #         uncovered.remove(prev)
            # prev = int(segments[1].strip())
            # first_record=True
        else:
            sys.stderr.write(
                "(WARNING) Unrecognized GCOV output: '%s'\n"
                "\tThis is indicitive of a gcov output parse error.\n"
                "\tPlease report this to the gcovr developers." % tmp
            )

        # save the code line to use it later with branches
        if is_code_statement:
            last_code_line = "".join(segments[2:])
            last_code_lineno = lineno
            last_code_line_excluded = False
            if excluding:
                last_code_line_excluded = True

        # clear the excluding flag for single-line excludes
        if excluding and not excluding[-1]:
            excluding.pop()

    if options.verbose:
        print('uncovered ' + str(uncovered))
        print('covered ' + str(covered))
        print('branches ' + str(branches))
        print('noncode ' + str(noncode))
    #
    # If the file is already in covdata, then we
    # remove lines that are covered here.  Otherwise,
    # initialize covdata
    #
    if fname not in covdata:
        covdata[fname] = CoverageData(
            fname, uncovered, uncovered_exceptional, covered, branches, noncode
        )
    else:
        covdata[fname].update(
            uncovered, uncovered_exceptional, covered, branches, noncode
        )
    INPUT.close()

    for header, line in excluding:
        sys.stderr.write("(WARNING) The coverage exclusion region start flag "
                         "%s_EXCL_START\n\ton line %d did not have "
                         "corresponding %s_EXCL_STOP flag\n\t in file %s.\n"
                         % (header, line, header, fname))


def log_warn(pattern, *args, **kwargs):
    """Write a formatted warning to STDERR.

    pattern: a str.format pattern
    args, kwargs: str.format arguments
    """
    pattern = "(WARNING) " + pattern + "\n"
    sys.stderr.write(pattern.format(*args, **kwargs))


def process_exclusion_marker(header, flag, exclusion_stack, lineno, fname):
    """Process the exclusion marker

    - START markers are added to the exclusion_stack
    - STOP markers remove a marker from the exclusion_stack
    - LINE markers return True

    returns: True when this line should be excluded, False for n/a.

    header: exclusion marker name, e.g. "LCOV" or "GCOVR"
    flag: exclusion marker action, one of "START", "STOP", or "LINE"
    exclusion_stack: list of (flag, lineno) tuples, will be modified
    lineno, fname: for error messages
    """
    if flag == 'START':
        exclusion_stack.append((header, lineno))
        return False

    if flag == 'STOP':
        if not exclusion_stack:
            log_warn(
                "mismatched coverage exclusion flags.\n"
                "\t{header}_EXCL_STOP found on line {lineno} "
                "without corresponding {header}_EXCL_START, "
                "when processing {fname}",
                header=header, lineno=lineno, fname=fname)
            return False

        start_header, start_line = exclusion_stack.pop()
        if header != start_header:
            log_warn(
                "{start_header}_EXCL_START found on line {start_line} "
                "was terminated by {header}_EXCL_STOP "
                "on line {lineno}, when processing {fname}",
                start_header=start_header, start_line=start_line,
                header=header, lineno=lineno, fname=fname)
        return False

    if flag == 'LINE':
        return True

    assert False, "unknown exclusion marker"  # pragma: no cover


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
