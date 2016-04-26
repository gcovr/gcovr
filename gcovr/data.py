# -*- coding:utf-8 -*-
#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________

import re
import os
import sys
import copy
import subprocess

from .path import search_file, aliases


output_re = re.compile("[Cc]reating [`'](.*)'$")
source_re = re.compile("[Cc]annot open (source|graph) file")

exclude_line_flag = "_EXCL_"
exclude_line_pattern = re.compile('([GL]COVR?)_EXCL_(LINE|START|STOP)')

c_style_comment_pattern = re.compile('/\*.*?\*/')
cpp_style_comment_pattern = re.compile('//.*?$')


#
# Container object for coverage statistics
#
class CoverageData(object):

    def __init__(
            self, fname, uncovered, uncovered_exceptional, covered, branches,
            noncode):
        self.fname = fname
        # Shallow copies are cheap & "safe" because the caller will
        # throw away their copies of covered & uncovered after calling
        # us exactly *once*
        self.uncovered = copy.copy(uncovered)
        self.uncovered_exceptional = copy.copy(uncovered_exceptional)
        self.covered = copy.copy(covered)
        self.noncode = copy.copy(noncode)
        # But, a deep copy is required here
        self.all_lines = copy.deepcopy(uncovered)
        self.all_lines.update(uncovered_exceptional)
        self.all_lines.update(covered.keys())
        self.branches = copy.deepcopy(branches)

    def update(
            self, uncovered, uncovered_exceptional, covered, branches,
            noncode):
        self.all_lines.update(uncovered)
        self.all_lines.update(uncovered_exceptional)
        self.all_lines.update(covered.keys())
        self.uncovered.update(uncovered)
        self.uncovered_exceptional.update(uncovered_exceptional)
        self.noncode.intersection_update(noncode)
        for k in covered.keys():
            self.covered[k] = self.covered.get(k, 0) + covered[k]
        for k in branches.keys():
            for b in branches[k]:
                d = self.branches.setdefault(k, {})
                d[b] = d.get(b, 0) + branches[k][b]
        self.uncovered.difference_update(self.covered.keys())
        self.uncovered_exceptional.difference_update(self.covered.keys())

    def uncovered_str(self, exceptional, options):
        if options.show_branch:
            #
            # Don't do any aggregation on branch results
            #
            tmp = []
            for line in self.branches.keys():
                for branch in self.branches[line]:
                    if self.branches[line][branch] == 0:
                        tmp.append(line)
                        break
            tmp.sort()
            return ",".join([str(x) for x in tmp]) or ""

        if exceptional:
            tmp = list(self.uncovered_exceptional)
        else:
            tmp = list(self.uncovered)
        if len(tmp) == 0:
            return ""

        #
        # Walk through the uncovered lines in sorted order.
        # Find blocks of consecutive uncovered lines, and return
        # a string with that information.
        #
        tmp.sort()
        first = None
        last = None
        ranges = []
        for item in tmp:
            if last is None:
                first = item
                last = item
            elif item == (last + 1):
                last = item
            else:
                #
                # Should we include noncode lines in the range of lines
                # to be covered???  This simplifies the ranges summary, but it
                # provides a counterintuitive listing.
                #
                #if len(self.noncode.intersection(range(last+1,item))) \
                #       == item - last - 1:
                #    last = item
                #    continue
                #
                if first == last:
                    ranges.append(str(first))
                else:
                    ranges.append(str(first) + "-" + str(last))
                first = item
                last = item
        if first == last:
            ranges.append(str(first))
        else:
            ranges.append(str(first) + "-" + str(last))
        return ",".join(ranges)

    def coverage(self, show_branch):
        if show_branch:
            total = 0
            cover = 0
            for line in self.branches.keys():
                for branch in self.branches[line].keys():
                    total += 1
                    cover += self.branches[line][branch] > 0 and 1 or 0
        else:
            total = len(self.all_lines)
            cover = len(self.covered)

        percent = total and str(int(100.0 * cover / total)) or "--"
        return (total, cover, percent)

    def summary(self, options):
        tmp = options.root_filter.sub('', self.fname)
        if not self.fname.endswith(tmp):
            # Do no truncation if the filter does not start matching at
            # the beginning of the string
            tmp = self.fname
        tmp = tmp.ljust(40)
        if len(tmp) > 40:
            tmp = tmp + "\n" + " " * 40

        (total, cover, percent) = self.coverage(options.show_branch)
        uncovered_lines = self.uncovered_str(False, options)
        if not options.show_branch:
            t = self.uncovered_str(True, options)
            if len(t):
                uncovered_lines += " [* " + t + "]"
        return (total, cover,
                tmp + str(total).rjust(8) + str(cover).rjust(8) +
                percent.rjust(6) + "%   " + uncovered_lines)


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
            files = search_file(".*\.gcov$", dir_)
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
            files = search_file(".*\.gc(da|no)$", dir_)
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


#
# Process a single gcov datafile
#
def process_gcov_data(data_fname, covdata, options):
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
    currdir = os.getcwd()
    os.chdir(options.root_dir)
    if sys.version_info >= (2, 6):
        fname = os.path.abspath((segments[-1]).strip())
    else:
        fname = aliases.unalias_path(os.path.abspath((segments[-1]).strip()))
    #
    # this fixes the problem on windows machines
    #
    fname = os.path.normcase(fname)

    os.chdir(currdir)
    if options.verbose:
        sys.stdout.write("Parsing coverage data for file %s\n" % fname)
    #
    # Return if the filename does not match the filter
    #
    filtered_fname = None
    for i in range(0, len(options.filter)):

        if options.verbose:
            sys.stdout.write("\n\nFilter: %s" % options.filter[i].pattern)
            sys.stdout.write("\nfname: %s" % fname)

        if options.filter[i].match(fname):
            filtered_fname = options.root_filter.sub('', fname)
            break
        else:
            if options.verbose:
                sys.stdout.write("\nno match")

    if options.verbose:
        sys.stdout.write("\n\n")

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
    # Parse each line, and record the lines
    # that are uncovered
    #
    excluding = []
    noncode = set()
    uncovered = set()
    uncovered_exceptional = set()
    covered = {}
    branches = {}
    #first_record=True
    lineno = 0
    last_code_line = ""
    last_code_lineno = 0
    last_code_line_excluded = False
    for line in INPUT:
        segments = line.split(":", 2)
        #print "\t","Y", segments
        tmp = segments[0].strip()
        if len(segments) > 1:
            try:
                lineno = int(segments[1].strip())
            except:
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
            if excluding or len(code) == 0 or code == "{" or code == "}" or \
                    code.startswith("//") or code == 'else':
                noncode.add(lineno)
        elif tmp[0] == '#':
            is_code_statement = True
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
                except:
                    count = 0
                branches.setdefault(lineno, {})[int(fields[1])] = count
        elif tmp.startswith('call'):
            pass
        elif tmp.startswith('function'):
            pass
        elif tmp[0] == 'f':
            pass
            #if first_record:
                #first_record=False
                #uncovered.add(prev)
            #if prev in uncovered:
                #tokens=re.split('[ \t]+',tmp)
                #if tokens[3] != "0":
                    #uncovered.remove(prev)
            #prev = int(segments[1].strip())
            #first_record=True
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

    ##print 'uncovered',uncovered
    ##print 'covered',covered
    ##print 'branches',branches
    ##print 'noncode',noncode
    #
    # If the file is already in covdata, then we
    # remove lines that are covered here.  Otherwise,
    # initialize covdata
    #
    if not fname in covdata:
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
    #print ""
    #print "PROCESS",filename
    #
    # Launch gcov
    #
    abs_filename = os.path.abspath(filename)
    dirname, fname = os.path.split(abs_filename)
    #(name,ext) = os.path.splitext(base)

    potential_wd = []
    errors = []
    Done = False

    if options.objdir:
        #print "X - objdir"
        src_components = abs_filename.split(os.sep)
        components = os.path.normpath(options.objdir).split(os.sep)
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
            # Revert to the normal
            #sys.exit(1)

    # no objdir was specified (or it was a parent dir); walk up the dir tree
    if len(potential_wd) == 0:
        potential_wd.append(options.root_dir)
        #print "X - potential_wd", root_dir
        wd = os.path.split(abs_filename)[0]
        while True:
            potential_wd.append(wd)
            wd = os.path.split(wd)[0]
            if wd == potential_wd[-1]:
                #
                # Stop at the root of the file system
                #
                break

    cmd = [
        options.gcov_cmd, abs_filename,
        "--branch-counts", "--branch-probabilities", "--preserve-paths",
        '--object-directory', dirname
    ]

    # NB: Currently, we will only parse English output
    env = dict(os.environ)
    env['LC_ALL'] = 'en_US'

    #print "HERE", potential_wd
    while len(potential_wd) > 0 and not Done:
        # NB: either len(potential_wd) == 1, or all entires are absolute
        # paths, so we don't have to chdir(starting_dir) at every
        # iteration.

        #
        # Iterate from the end of the potential_wd list, which is the root
        # directory
        #
        dir_ = potential_wd.pop(0)
        #print "X DIR:", dir_
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
        gcov_files = {'active' : [], 'filter' : [], 'exclude' : []}
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

        #print "HERE", err, "XXX", source_re.search(err)
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
                process_gcov_data(fname, covdata, options)
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
    if not options.gcov_filter.match(filename):
        if options.verbose:
            sys.stdout.write("Filtering gcov file %s\n" % filename)
        return

    for exc in options.gcov_exclude:
        if exc.match(options.gcov_filter.sub('', filename)) or \
                exc.match(filename) or \
                exc.match(os.path.abspath(filename)):
            if options.verbose:
                sys.stdout.write("Excluding gcov file %s\n" % filename)
            return

    process_gcov_data(filename, covdata, options)

    if not options.keep:
        if os.path.exists(filename):
            # Only remove files that actually exist.
            os.remove(filename)


def get_coverage_data(paths, options):

    # Get data files
    datafiles = get_datafiles(paths, options)

    # Get coverage data
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

    return covdata
