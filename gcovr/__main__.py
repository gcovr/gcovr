# -*- coding:utf-8 -*-
#
# A report generator for gcov 3.4
#
# This routine generates a format that is similar to the format generated
# by the Python coverage.py module.  This code is similar to the
# data processing performed by lcov's geninfo command.  However, we
# don't worry about parsing the *.gcna files, and backwards compatibility for
# older versions of gcov is not supported.
#
# Outstanding issues
#   - verify that gcov 3.4 or newer is being used
#   - verify support for symbolic links
#
# For documentation, bug reporting, and updates,
# see http://gcovr.com/
#
#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
# _________________________________________________________________________
#
# $Revision$
# $Date$
#

import copy
import os
import re
import subprocess
import sys
import time
import xml.dom.minidom

from optparse import Option, OptionParser, OptionValueError
from os.path import normpath

from .coverage import CoverageData
from .html_generator import print_html_report
from .utils import (
    aliases, search_file, get_global_stats, calculate_coverage, build_filter)
from .version import __version__, version_str

try:
    xrange
except NameError:
    xrange = range

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
                if flag == 'START':
                    excluding.append((header, lineno))
                elif flag == 'STOP':
                    if excluding:
                        _header, _line = excluding.pop()
                        if _header != header:
                            sys.stderr.write(
                                "(WARNING) %s_EXCL_START found on line %s "
                                "was terminated by %s_EXCL_STOP on line %s, "
                                "when processing %s\n"
                                % (_header, _line, header, lineno, fname)
                            )
                    else:
                        sys.stderr.write(
                            "(WARNING) mismatched coverage exclusion flags.\n"
                            "\t%s_EXCL_STOP found on line %s without "
                            "corresponding %s_EXCL_START, when processing %s\n"
                            % (header, lineno, header, fname)
                        )
                elif flag == 'LINE':
                    # We buffer the line exclusion so that it is always
                    # the last thing added to the exclusion list (and so
                    # only ONE is ever added to the list).  This guards
                    # against cases where puts a _LINE and _START (or
                    # _STOP) on the same line... it also guards against
                    # duplicate _LINE flags.
                    excl_line = True
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


#
# Produce the classic gcovr text report
#
def print_text_report(covdata, options):
    def _num_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        return total - covered

    def _percent_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        if covered:
            return -1.0 * covered / total
        else:
            return total or 1e6

    def _alpha(key):
        return key

    if options.output:
        OUTPUT = open(options.output, 'w')
    else:
        OUTPUT = sys.stdout
    total_lines = 0
    total_covered = 0

    # Header
    OUTPUT.write("-" * 78 + '\n')
    OUTPUT.write(" " * 27 + "GCC Code Coverage Report\n")
    OUTPUT.write("Directory: " + options.root + "\n")

    OUTPUT.write("-" * 78 + '\n')
    a = options.show_branch and "Branches" or "Lines"
    b = options.show_branch and "Taken" or "Exec"
    c = "Missing"
    OUTPUT.write(
        "File".ljust(40) + a.rjust(8) + b.rjust(8) + "  Cover   " + c + "\n"
    )
    OUTPUT.write("-" * 78 + '\n')

    # Data
    keys = list(covdata.keys())
    keys.sort(
        key=options.sort_uncovered and _num_uncovered or
        options.sort_percent and _percent_uncovered or _alpha
    )

    def _summarize_file_coverage(coverage):
        tmp = options.root_filter.sub('', coverage.fname)
        if not coverage.fname.endswith(tmp):
            # Do no truncation if the filter does not start matching at
            # the beginning of the string
            tmp = coverage.fname
        tmp = tmp.replace('\\', '/').ljust(40)
        if len(tmp) > 40:
            tmp = tmp + "\n" + " " * 40

        (total, cover, percent) = coverage.coverage(options.show_branch)
        uncovered_lines = coverage.uncovered_str(
            exceptional=False, show_branch=options.show_branch)
        if not options.show_branch:
            t = coverage.uncovered_str(
                exceptional=True, show_branch=options.show_branch)
            if len(t):
                uncovered_lines += " [* " + t + "]"
        return (total, cover,
                tmp + str(total).rjust(8) + str(cover).rjust(8) +
                percent.rjust(6) + "%   " + uncovered_lines)

    for key in keys:
        (t, n, txt) = _summarize_file_coverage(covdata[key])
        total_lines += t
        total_covered += n
        OUTPUT.write(txt + '\n')

    # Footer & summary
    OUTPUT.write("-" * 78 + '\n')
    percent = calculate_coverage(total_covered, total_lines, nan_value=None)
    percent = "--" if percent is None else str(int(percent))
    OUTPUT.write(
        "TOTAL".ljust(40) + str(total_lines).rjust(8) +
        str(total_covered).rjust(8) + str(percent).rjust(6) + "%" + '\n'
    )
    OUTPUT.write("-" * 78 + '\n')

    # Close logfile
    if options.output:
        OUTPUT.close()


#
# Prints a small report to the standard output
#
def print_summary(covdata):
    (lines_total, lines_covered, percent,
        branches_total, branches_covered,
        percent_branches) = get_global_stats(covdata)

    lines_out = "lines: %0.1f%% (%s out of %s)\n" % (
        percent, lines_covered, lines_total
    )
    branches_out = "branches: %0.1f%% (%s out of %s)\n" % (
        percent_branches, branches_covered, branches_total
    )

    sys.stdout.write(lines_out)
    sys.stdout.write(branches_out)


#
# Exits with status 2 if below threshold
#
def fail_under(covdata, threshold_line, threshold_branch):
    (lines_total, lines_covered, percent,
        branches_total, branches_covered,
        percent_branches) = get_global_stats(covdata)

    if branches_total == 0:
        percent_branches = 100.0

    if percent < threshold_line and percent_branches < threshold_branch:
        sys.exit(6)
    if percent < threshold_line:
        sys.exit(2)
    if percent_branches < threshold_branch:
        sys.exit(4)


#
# Produce an XML report in the Cobertura format
#
def print_xml_report(covdata, options):
    branchTotal = 0
    branchCovered = 0
    lineTotal = 0
    lineCovered = 0

    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=True)
        branchTotal += total
        branchCovered += covered

    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=False)
        lineTotal += total
        lineCovered += covered

    impl = xml.dom.minidom.getDOMImplementation()
    docType = impl.createDocumentType(
        "coverage", None,
        "http://cobertura.sourceforge.net/xml/coverage-04.dtd"
    )
    doc = impl.createDocument(None, "coverage", docType)
    root = doc.documentElement
    root.setAttribute(
        "line-rate", lineTotal == 0 and '0.0' or
        str(float(lineCovered) / lineTotal)
    )
    root.setAttribute(
        "branch-rate", branchTotal == 0 and '0.0' or
        str(float(branchCovered) / branchTotal)
    )
    root.setAttribute(
        "lines-covered", str(lineCovered)
    )
    root.setAttribute(
        "lines-valid", str(lineTotal)
    )
    root.setAttribute(
        "branches-covered", str(branchCovered)
    )
    root.setAttribute(
        "branches-valid", str(branchTotal)
    )
    root.setAttribute(
        "complexity", "0.0"
    )
    root.setAttribute(
        "timestamp", str(int(time.time()))
    )
    root.setAttribute(
        "version", "gcovr %s" % (version_str(),)
    )

    # Generate the <sources> element: this is either the root directory
    # (specified by --root), or the CWD.
    sources = doc.createElement("sources")
    root.appendChild(sources)

    # Generate the coverage output (on a per-package basis)
    packageXml = doc.createElement("packages")
    root.appendChild(packageXml)
    packages = {}
    source_dirs = set()

    keys = list(covdata.keys())
    keys.sort()
    for f in keys:
        data = covdata[f]
        directory = options.root_filter.sub('', f)
        if f.endswith(directory):
            src_path = f[:-1 * len(directory)]
            if len(src_path) > 0:
                while directory.startswith(os.path.sep):
                    src_path += os.path.sep
                    directory = directory[len(os.path.sep):]
                source_dirs.add(src_path)
        else:
            # Do no truncation if the filter does not start matching at
            # the beginning of the string
            directory = f
        directory, fname = os.path.split(directory)

        package = packages.setdefault(
            directory, [doc.createElement("package"), {}, 0, 0, 0, 0]
        )
        c = doc.createElement("class")
        # The Cobertura DTD requires a methods section, which isn't
        # trivial to get from gcov (so we will leave it blank)
        c.appendChild(doc.createElement("methods"))
        lines = doc.createElement("lines")
        c.appendChild(lines)

        class_lines = 0
        class_hits = 0
        class_branches = 0
        class_branch_hits = 0
        for line in sorted(data.all_lines):
            hits = data.covered.get(line, 0)
            class_lines += 1
            if hits > 0:
                class_hits += 1
            L = doc.createElement("line")
            L.setAttribute("number", str(line))
            L.setAttribute("hits", str(hits))
            branches = data.branches.get(line)
            if branches is None:
                L.setAttribute("branch", "false")
            else:
                b_hits = 0
                for v in branches.values():
                    if v > 0:
                        b_hits += 1
                coverage = 100 * b_hits / len(branches)
                L.setAttribute("branch", "true")
                L.setAttribute(
                    "condition-coverage",
                    "%i%% (%i/%i)" % (coverage, b_hits, len(branches))
                )
                cond = doc.createElement('condition')
                cond.setAttribute("number", "0")
                cond.setAttribute("type", "jump")
                cond.setAttribute("coverage", "%i%%" % (coverage))
                class_branch_hits += b_hits
                class_branches += float(len(branches))
                conditions = doc.createElement("conditions")
                conditions.appendChild(cond)
                L.appendChild(conditions)

            lines.appendChild(L)

        className = fname.replace('.', '_')
        c.setAttribute("name", className)
        c.setAttribute("filename", os.path.join(directory, fname).replace('\\', '/'))
        c.setAttribute(
            "line-rate",
            str(class_hits / (1.0 * class_lines or 1.0))
        )
        c.setAttribute(
            "branch-rate",
            str(class_branch_hits / (1.0 * class_branches or 1.0))
        )
        c.setAttribute("complexity", "0.0")

        package[1][className] = c
        package[2] += class_hits
        package[3] += class_lines
        package[4] += class_branch_hits
        package[5] += class_branches

    keys = list(packages.keys())
    keys.sort()
    for packageName in keys:
        packageData = packages[packageName]
        package = packageData[0]
        packageXml.appendChild(package)
        classes = doc.createElement("classes")
        package.appendChild(classes)
        classNames = list(packageData[1].keys())
        classNames.sort()
        for className in classNames:
            classes.appendChild(packageData[1][className])
        package.setAttribute("name", packageName.replace(os.sep, '.'))
        package.setAttribute(
            "line-rate", str(packageData[2] / (1.0 * packageData[3] or 1.0))
        )
        package.setAttribute(
            "branch-rate", str(packageData[4] / (1.0 * packageData[5] or 1.0))
        )
        package.setAttribute("complexity", "0.0")

    # Populate the <sources> element: this is the root directory
    source = doc.createElement("source")
    source.appendChild(doc.createTextNode(options.root.strip()))
    sources.appendChild(source)

    if options.prettyxml:
        import textwrap
        lines = doc.toprettyxml(" ").split('\n')
        for i in xrange(len(lines)):
            n = 0
            while n < len(lines[i]) and lines[i][n] == " ":
                n += 1
            lines[i] = "\n".join(textwrap.wrap(
                lines[i], 78,
                break_long_words=False,
                break_on_hyphens=False,
                subsequent_indent=" " + n * " "
            ))
        xmlString = "\n".join(lines)
        # print textwrap.wrap(doc.toprettyxml(" "), 80)
    else:
        xmlString = doc.toprettyxml(indent="")
    if options.output is None:
        sys.stdout.write(xmlString + '\n')
    else:
        OUTPUT = open(options.output, 'w')
        OUTPUT.write(xmlString + '\n')
        OUTPUT.close()


# #
# # MAIN
# #

# helper for percentage actions
def check_percentage(option, opt, value):
    try:
        x = float(value)
        if not (0.0 <= x <= 100.0):
            raise ValueError()
    except ValueError:
        raise OptionValueError("option %s: %r not in range [0.0, 100.0]" % (opt, value))
    return x


class PercentageOption (Option):
    TYPES = Option.TYPES + ("percentage",)
    TYPE_CHECKER = copy.copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["percentage"] = check_percentage


def parse_arguments(args):
    """
    Create and parse arguments.
    """
    parser = OptionParser(option_class=PercentageOption)
    parser.add_option(
        "--version",
        help="Print the version number, then exit",
        action="store_true",
        dest="version",
        default=False
    )
    parser.add_option(
        "-v", "--verbose",
        help="Print progress messages",
        action="store_true",
        dest="verbose",
        default=False
    )
    parser.add_option(
        '--object-directory',
        help="Specify the directory that contains the gcov data files.  gcovr "
             "must be able to identify the path between the *.gcda files and the "
             "directory where gcc was originally run.  Normally, gcovr can guess "
             "correctly.  This option overrides gcovr's normal path detection and "
             "can specify either the path from gcc to the gcda file (i.e. what "
             "was passed to gcc's '-o' option), or the path from the gcda file to "
             "gcc's original working directory.",
        action="store",
        dest="objdir",
        default=None
    )
    parser.add_option(
        "-o", "--output",
        help="Print output to this filename",
        action="store",
        dest="output",
        default=None
    )
    parser.add_option(
        "-k", "--keep",
        help="Keep the temporary *.gcov files generated by gcov.  "
             "By default, these are deleted.",
        action="store_true",
        dest="keep",
        default=False
    )
    parser.add_option(
        "-d", "--delete",
        help="Delete the coverage files after they are processed.  "
             "These are generated by the users's program, and by default gcovr "
             "does not remove these files.",
        action="store_true",
        dest="delete",
        default=False
    )
    parser.add_option(
        "-f", "--filter",
        help="Keep only the data files that match this regular expression",
        action="append",
        dest="filter",
        default=[]
    )
    parser.add_option(
        "-e", "--exclude",
        help="Exclude data files that match this regular expression",
        action="append",
        dest="exclude",
        default=[]
    )
    parser.add_option(
        "--gcov-filter",
        help="Keep only gcov data files that match this regular expression",
        action="store",
        dest="gcov_filter",
        default=None
    )
    parser.add_option(
        "--gcov-exclude",
        help="Exclude gcov data files that match this regular expression",
        action="append",
        dest="gcov_exclude",
        default=[]
    )
    parser.add_option(
        "-r", "--root",
        help="Defines the root directory for source files.  "
             "This is also used to filter the files, and to standardize "
             "the output.",
        action="store",
        dest="root",
        default='.'
    )
    parser.add_option(
        "-x", "--xml",
        help="Generate XML instead of the normal tabular output.",
        action="store_true",
        dest="xml",
        default=False
    )
    parser.add_option(
        "--xml-pretty",
        help="Generate pretty XML instead of the normal dense format.",
        action="store_true",
        dest="prettyxml",
        default=False
    )
    parser.add_option(
        "--html",
        help="Generate HTML instead of the normal tabular output.",
        action="store_true",
        dest="html",
        default=False
    )
    parser.add_option(
        "--html-details",
        help="Generate HTML output for source file coverage.",
        action="store_true",
        dest="html_details",
        default=False
    )
    parser.add_option(
        "--html-absolute-paths",
        help="Set the paths in the HTML report to be absolute instead "
             "of relative",
        action="store_false",
        dest="relative_anchors",
        default=True
    )
    parser.add_option(
        '--html-encoding',
        help='HTML file encoding (default: UTF-8).',
        action='store',
        dest='html_encoding',
        default='UTF-8'
    )
    parser.add_option(
        "-b", "--branches",
        help="Tabulate the branch coverage instead of the line coverage.",
        action="store_true",
        dest="show_branch",
        default=None
    )
    parser.add_option(
        "-u", "--sort-uncovered",
        help="Sort entries by increasing number of uncovered lines.",
        action="store_true",
        dest="sort_uncovered",
        default=None
    )
    parser.add_option(
        "-p", "--sort-percentage",
        help="Sort entries by decreasing percentage of covered lines.",
        action="store_true",
        dest="sort_percent",
        default=None
    )
    parser.add_option(
        "--gcov-executable",
        help="Defines the name/path to the gcov executable [defaults to the "
             "GCOV environment variable, if present; else 'gcov'].",
        action="store",
        dest="gcov_cmd",
        default=os.environ.get('GCOV', 'gcov')
    )
    parser.add_option(
        "--exclude-unreachable-branches",
        help="Exclude from coverage branches which are marked to be excluded "
             "by LCOV/GCOV markers or are determined to be from lines "
             "containing only compiler-generated \"dead\" code.",
        action="store_true",
        dest="exclude_unreachable_branches",
        default=False
    )
    parser.add_option(
        "--exclude-directories",
        help="Exclude directories from search path that match this regular expression",
        action="append",
        dest="exclude_dirs",
        default=[]
    )
    parser.add_option(
        "-g", "--use-gcov-files",
        help="Use preprocessed gcov files for analysis.",
        action="store_true",
        dest="gcov_files",
        default=False
    )
    parser.add_option(
        "-s", "--print-summary",
        help="Prints a small report to stdout with line & branch "
             "percentage coverage",
        action="store_true",
        dest="print_summary",
        default=False
    )
    parser.add_option(
        "--fail-under-line",
        type="percentage",
        metavar="MIN",
        help="Exit with a status of 2 if the total line coverage is less "
             "than MIN. "
             "Can be ORed with exit status of '--fail-under-branch' option",
        action="store",
        dest="fail_under_line",
        default=0.0
    )
    parser.add_option(
        "--fail-under-branch",
        type="percentage",
        metavar="MIN",
        help="Exit with a status of 4 if the total branch coverage is less "
             "than MIN. "
             "Can be ORed with exit status of '--fail-under-line' option",
        action="store",
        dest="fail_under_branch",
        default=0.0
    )
    parser.usage = "gcovr [options]"
    parser.description = \
        "A utility to run gcov and generate a simple report that summarizes " \
        "the coverage"

    return parser.parse_args(args=args)


def main(args=None):
    global options
    options, args = parse_arguments(args)

    if options.version:
        sys.stdout.write(
            "gcovr %s\n"
            "\n"
            "Copyright (2013) Sandia Corporation. Under the terms of Contract\n"
            "DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government\n"
            "retains certain rights in this software.\n"
            % (version_str(), )
        )
        sys.exit(0)

    if options.output is not None:
        options.output = os.path.abspath(options.output)

    if options.objdir is not None:
        if not options.objdir:
            sys.stderr.write(
                "(ERROR) empty --object-directory option.\n"
                "\tThis option specifies the path to the object file "
                "directory of your project.\n"
                "\tThis option cannot be an empty string.\n"
            )
            sys.exit(1)
        tmp = options.objdir.replace('/', os.sep).replace('\\', os.sep)
        while os.sep + os.sep in tmp:
            tmp = tmp.replace(os.sep + os.sep, os.sep)
        if normpath(options.objdir) != tmp:
            sys.stderr.write(
                "(WARNING) relative referencing in --object-directory.\n"
                "\tthis could cause strange errors when gcovr attempts to\n"
                "\tidentify the original gcc working directory.\n")
        if not os.path.exists(normpath(options.objdir)):
            sys.stderr.write(
                "(ERROR) Bad --object-directory option.\n"
                "\tThe specified directory does not exist.\n")
            sys.exit(1)

    options.starting_dir = os.path.abspath(os.getcwd())
    if not options.root:
        sys.stderr.write(
            "(ERROR) empty --root option.\n"
            "\tRoot specifies the path to the root "
            "directory of your project.\n"
            "\tThis option cannot be an empty string.\n"
        )
        sys.exit(1)
    options.root_dir = os.path.abspath(options.root)

    #
    # Setup filters
    #

    for i in range(0, len(options.exclude)):
        options.exclude[i] = build_filter(options.exclude[i])

    if options.exclude_dirs is not None:
        for i in range(0, len(options.exclude_dirs)):
            options.exclude_dirs[i] = build_filter(options.exclude_dirs[i])

    options.root_filter = re.compile(re.escape(options.root_dir + os.sep))
    for i in range(0, len(options.filter)):
        options.filter[i] = build_filter(options.filter[i])
    if len(options.filter) == 0:
        options.filter.append(options.root_filter)

    for i in range(0, len(options.gcov_exclude)):
        options.gcov_exclude[i] = build_filter(options.gcov_exclude[i])
    if options.gcov_filter is not None:
        options.gcov_filter = build_filter(options.gcov_filter)
    else:
        options.gcov_filter = re.compile('')
    #
    # Get data files
    #
    if len(args) == 0:
        search_paths = [options.root]

        if options.objdir is not None:
            search_paths.append(options.objdir)

        datafiles = get_datafiles(search_paths, options)
    else:
        datafiles = get_datafiles(args, options)
    #
    # Get coverage data
    #
    covdata = {}
    for file_ in datafiles:
        if options.gcov_files:
            process_existing_gcov_file(file_, covdata, options)
        else:
            process_datafile(file_, covdata, options)
    if options.verbose:
        sys.stdout.write(
            "Gathered coveraged data for " + str(len(covdata)) + " files\n"
        )
    #
    # Print report
    #
    if options.xml or options.prettyxml:
        print_xml_report(covdata, options)
    elif options.html or options.html_details:
        print_html_report(covdata, options)
    else:
        print_text_report(covdata, options)

    if options.print_summary:
        print_summary(covdata, options)

    if options.fail_under_line > 0.0 or options.fail_under_branch > 0.0:
        fail_under(covdata, options.fail_under_line, options.fail_under_branch)


if __name__ == '__main__':
    main()
