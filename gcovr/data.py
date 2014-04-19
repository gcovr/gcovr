#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________


import copy
import os
import re
import sre_compile
import sre_constants
import sre_parse
import subprocess
import sys
import textwrap


output_re = re.compile("[Cc]reating [`'](.*)'$")
source_re = re.compile("cannot open (source|graph) file")


def is_gcno(path):
    _, ext = os.path.splitext(path)
    return ext == ".gcno"


def is_gcda(path):
    _, ext = os.path.splitext(path)
    return ext == ".gcda"


#
# Errors encountered during execution of GCOV.
#
class GcovError(RuntimeError):
    def __init__(self, message, filename):
        super(RuntimeError, self).__init__(message)
        self.filename = filename


class GcovParserError(ValueError):
    def __init__(self, string):
        super(ValueError, self).__init__(
            "Unrecognized GCOV output: '%s'" % string)


class ParameterValueError(ValueError):
    def __init__(self, parameter, value, message):
        msg = (["Setting %s to %s resulted in an error:" % (parameter, value)]
               + textwrap.wrap(message))
        super(ValueError, self).__init__("\n    ".join(msg))


#
# Container object for coverage statistics
#
class CoverageData(object):

    def __init__(self, fname, uncovered, uncovered_exceptional, covered,
                 branches, noncode):
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

    def update(self, uncovered, uncovered_exceptional, covered, branches,
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

    def uncovered_str(self, exceptional, show_branch):
        if show_branch:
            # Don't do any aggregation on branch results
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

        tmp.sort()
        first = None
        last = None
        ranges = []
        for item in tmp:
            if last is None:
                first = item
                last = item
            elif item == (last+1):
                last = item
            else:
                item_range = range(last + 1, item)
                items_left = len(self.noncode.intersection(item_range))
                if items_left == item - last - 1:
                    last = item
                    continue

                if first == last:
                    ranges.append(str(first))
                else:
                    ranges.append(str(first)+"-"+str(last))
                first = item
                last = item
        if first == last:
            ranges.append(str(first))
        else:
            ranges.append(str(first)+"-"+str(last))
        return ",".join(ranges)

    def coverage(self, show_branch):
        if (show_branch):
            total = 0
            cover = 0
            for line in self.branches.keys():
                for branch in self.branches[line].keys():
                    total += 1
                    cover += self.branches[line][branch] > 0 and 1 or 0
        else:
            total = len(self.all_lines)
            cover = len(self.covered)

        percent = total and str(int(100.0*cover/total)) or "--"
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
        uncovered_lines = self.uncovered_str(False, options.show_branch)
        if not options.show_branch:
            t = self.uncovered_str(True, False)
            if len(t):
                uncovered_lines += " [* " + t + "]"

        txt = "".join([tmp, str(total).rjust(8), str(cover).rjust(8),
                       percent.rjust(6), "%   ", uncovered_lines])
        return (total, cover, txt)


class GcovParser(object):
    exclude_line_pattern = re.compile('([GL]COVR?)_EXCL_(LINE|START|STOP)')
    c_style_comment_pattern = re.compile('/\*.*?\*/')
    cpp_style_comment_pattern = re.compile('//.*?$')

    class _State(object):
        is_code_statement = False
        filename = None
        uncovered = set()
        uncovered_exceptional = set()
        covered = {}
        branches = {}
        excluding = []
        segments = []
        noncode = set()
        lineno = 0
        last_code_line = ""
        last_code_lineno = 0
        last_code_line_excluded = False

    def __init__(self, root_dir, file_filter, root_filter, exclude,
                 exclude_unreachable_branches, verbose=False):
        self.root_dir = root_dir
        self.file_filter = file_filter
        self.root_filter = root_filter
        self.exclude = exclude
        self.exclude_unreachable_branches = exclude_unreachable_branches
        self.verbose = verbose

        self._lexicon, self._scanner = self._build_scanner()

    def _build_scanner(self):
        lexicon = [
            (r'^-.*', self._s_code),
            (r'^#.*', self._s_uncovered),
            (r'^=.*', self._s_uncovered_exceptional),
            (r'^\d.*', self._s_covered),
            (r'^branch.*', self._s_branch),
            (r'^call.*', self._s_call),
            (r'^function.*', self._s_function),
            (r'^f.*', self._s_f),
            (r'.*_EXCL_.*', self._s_exclude)]
        parser = []
        pattern = sre_parse.Pattern()
        for phrase, action in lexicon:
            data = [(sre_constants.SUBPATTERN,
                     (len(parser) + 1, sre_parse.parse(phrase, 0)))]
            parser.append(sre_parse.SubPattern(pattern, data))
        pattern.groups = len(parser) + 1
        data = [(sre_parse.BRANCH, (None, parser))]
        parser = sre_parse.SubPattern(pattern, data)
        return lexicon, sre_compile.compile(parser)

    def _s_code(self, state, match):
        state.is_code_statement = True
        code = state.segments[2].strip()
        # remember certain non-executed lines
        zero_len = len(code) == 0
        is_bracket = code == '{' or code == '}'
        is_comment = code.startswith('//')
        is_else = code == 'else'
        if state.excluding or zero_len or is_bracket or is_comment or is_else:
            state.noncode.add(state.lineno)

    def _s_uncovered(self, state, match):
        if state.excluding:
            return self._s_code(state, match)
        state.is_code_statement = True
        state.uncovered.add(state.lineno)

    def _s_uncovered_exceptional(self, state, match):
        if state.excluding:
            return self._s_code(state, match)
        state.is_code_statement = True
        state.uncovered_exceptional.add(state.lineno)

    def _s_covered(self, state, match):
        if state.excluding:
            return self._s_code(state, match)
        state.is_code_statement = True
        state.covered[state.lineno] = int(state.segments[0].strip())

    def _s_branch(self, state, match):
        exclude_branch = False
        on_last_code_line = state.lineno == state.last_code_lineno
        if self.exclude_unreachable_branches and on_last_code_line:
            if state.last_code_line_excluded:
                exclude_branch = True
                exclude_reason = "marked with exclude pattern"
            else:
                code = state.last_code_line
                code = re.sub(GcovParser.cpp_style_comment_pattern, '', code)
                code = re.sub(GcovParser.c_style_comment_pattern, '', code)
                code = code.strip()
                code_nospace = code.replace(' ', '')
                exclude_branch = len(code) == 0
                exclude_branch = exclude_branch or code == '{'
                exclude_branch = exclude_branch or code == '}'
                exclude_branch = exclude_branch or code_nospace == '{}'
                exclude_reason = "detected as compiler-generated code"

        if exclude_branch:
            if self.verbose:
                sys.stdout.write("Excluding unreachable branch on "
                                 "line %d in file %s (%s).\n"
                                 % (state.lineno, state.filename,
                                    exclude_reason))
            else:
                fields = match.string.split()
                try:
                    count = int(fields[3])
                    field = int(fields[1])
                    state.branches.setdefault(state.lineno, {})[field] = count
                except:
                    # We ignore branches that were "never executed"
                    pass

    def _s_call(self, state, match):
        pass

    def _s_function(self, state, match):
        pass

    def _s_f(self, state, match):
        pass

    def _s_exclude(self, state, match):
        excl_line = False
        pattern = GcovParser.exclude_line_pattern
        for header, flag in pattern.findall(match.string):
            if flag == 'START':
                state.excluding.append((header, state.lineno))
            elif flag == 'STOP':
                if state.excluding:
                    header, line = state.excluding.pop()
                    if header != header:
                        sys.stderr.write(
                            "(WARNING) %s_EXCL_START found on line %s "
                            "was terminated by %s_EXCL_STOP on line %s, "
                            "when processing %s\n"
                            % (header, line, header, state.lineno,
                               state.filename))
                else:
                    sys.stderr.write(
                        "(WARNING) mismatched coverage exclusion flags.\n"
                        "\t%s_EXCL_STOP found on line %s without "
                        "corresponding %s_EXCL_START, when processing %s\n"
                        % (header, state.lineno, header, state.filename))
            elif flag == 'LINE':
                # We buffer the line exclusion so that it is always
                # the last thing added to the exclusion list (and so
                # only ONE is ever added to the list).  This guards
                # against cases where puts a _LINE and _START (or
                # _STOP) on the same line... it also guards against
                # duplicate _LINE flags.
                excl_line = True
        if excl_line:
            state.excluding.append(False)

    def _scan(self, string, state):
        match = self._scanner.scanner(string).match()
        i = 0
        while True:
            if not match:
                raise GcovParserError(string)
            j = match.end()
            if i == j:
                break
            self._lexicon[match.lastindex - 1][1](state, match)
            i = j

    def _parse_line(self, state, line):
        state.segments = line.split(":", 2)
        if len(state.segments) > 1:
            try:
                state.lineno = int(state.segments[1].strip())
            except:
                pass  # keep previous line number!

        self._scan(state.segments[0].strip(), state)

        # save the code line to use it later with branches
        if state.is_code_statement:
            state.last_code_line = "".join(state.segments[2:])
            state.last_code_lineno = state.lineno
            state.last_code_line_excluded = False
            if state.excluding:
                state.last_code_line_excluded = True

        # clear the excluding flag for single-line excludes
        if state.excluding and not state.excluding[-1]:
            state.excluding.pop()

    def _update_coverage_data(self, state, coverage_data):
        if not state.filename in coverage_data:
            data = CoverageData(state.filename, state.uncovered,
                                state.uncovered_exceptional, state.covered,
                                state.branches, state.noncode)
            coverage_data[state.filename] = data
        else:
            coverage_data[state.filename].update(state.uncovered,
                                                 state.uncovered_exceptional,
                                                 state.covered, state.branches,
                                                 state.noncode)

    def _is_excluded_file(self, filename):
        filtered_fname = None
        for i in range(0, len(self.file_filter)):
            if self.file_filter[i].match(filename):
                filtered_fname = self.root_filter.sub('', filename)
                break
        if filtered_fname is None:
            if self.verbose:
                sys.stdout.write("  Filtering coverage data for file %s\n"
                                 % filename)
            return True

        for i in range(0, len(self.exclude)):
            excluded = False
            if filtered_fname is not None:
                excluded = excluded or self.exclude[i].match(filtered_fname)
            excluded = excluded or self.exclude[i].match(filename)
            abs_path = os.path.abspath(filename)
            excluded = excluded or self.exclude[i].match(abs_path)

            if excluded:
                if self.verbose:
                    sys.stdout.write("  Excluding coverage data for file %s\n"
                                     % filename)
                return True
        return False

    def parse(self, filename, coverage_data):
        file_input = open(filename, "r")
        state = GcovParser._State()
        # Get the filename
        try:
            line = file_input.readline()
        except:
            print(file_input)
            raise

        state.segments = line.split(':', 3)
        ends_with_source = state.segments[2].lower().strip().endswith('source')
        if len(state.segments) != 4 or not ends_with_source:
            raise GcovParserError(line.rstrip())

        currdir = os.getcwd()
        os.chdir(self.root_dir)
        state.filename = os.path.abspath((state.segments[-1]).strip())
        os.chdir(currdir)
        if self.verbose:
            sys.stdout.write("Parsing coverage data for file %s\n"
                             % state.filename)

        if self._is_excluded_file(state.filename):
            return

        for line in file_input:
            self._parse_line(state, line)
        file_input.close()

        self._update_coverage_data(state, coverage_data)

        for header, line in state.excluding:
            sys.stderr.write("(WARNING) The coverage exclusion region start "
                             "flag %s_EXCL_START\n\ton line %d did not have "
                             "corresponding %s_EXCL_STOP flag\n\t in file %s."
                             "\n" % (header, line, header, state.filename))


def find_gcov_files(gcov_filter, gcov_exclude, gcov_stdout, verbose=False):
    gcov_files = {'active': [], 'filter': [], 'exclude': []}
    for line in gcov_stdout.splitlines():
        found = output_re.search(line.strip())
        if found is not None:
            fname = found.group(1)
            if not gcov_filter.match(fname):
                if verbose:
                    sys.stdout.write("Filtering gcov file %s\n" % fname)
                gcov_files['filter'].append(fname)
                continue
            exclude = False
            for i in range(0, len(gcov_exclude)):
                current_exclude = gcov_exclude[i]
                filtered_fname = gcov_filter.sub('', fname)
                exclude = exclude or current_exclude.match(filtered_fname)
                exclude = exclude or current_exclude.match(fname)
                absolute_path = os.path.abspath(fname)
                exclude = exclude or current_exclude.match(absolute_path)
                if exclude:
                    break
            if not exclude:
                gcov_files['active'].append(fname)
            elif verbose:
                sys.stdout.write("Excluding gcov file %s\n" % fname)
                gcov_files['exclude'].append(fname)

    return gcov_files


def find_potential_wd(objdir, abs_filename):
    potential_wd = []

    if objdir:
        src_components = abs_filename.split(os.sep)
        components = os.path.normpath(objdir).split(os.sep)
        idx = 1
        while idx <= len(components):
            if idx > len(src_components):
                break
            if components[-1*idx] != src_components[-1*idx]:
                break
            idx += 1
        if idx > len(components):
            pass  # a parent dir; the normal process will find it
        elif components[-1*idx] == '..':
            # NB: os.path.join does not re-add leading '/' characters!?!
            dirs = [os.path.sep.join(src_components[:len(src_components)-idx])]
            while idx <= len(components) and components[-1*idx] == '..':
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
                tmp = [objdir]
            else:
                # relative path: check relative to both the cwd and the
                # gcda file
                tmp = [os.path.join(x, objdir) for x in
                       [os.path.dirname(abs_filename), os.getcwd()]]
            potential_wd = [testdir for testdir in tmp
                            if os.path.isdir(testdir)]
            if len(potential_wd) == 0:
                raise ParameterValueError('object-directory', objdir,
                                          "Cannot identify the location where "
                                          "compiler was run.")

    # no objdir was specified (or it was a parent dir); walk up the dir tree
    if len(potential_wd) == 0:
        wd = os.path.split(abs_filename)[0]
        while True:
            potential_wd.append(wd)
            wd = os.path.split(wd)[0]
            if wd == potential_wd[-1]:
                break

    return potential_wd


class Gcov(object):
    def __init__(self, gcov_cmd, abs_filename, verbose=False):
        (dirname, self.filename) = os.path.split(abs_filename)
        self.cmd = [gcov_cmd, abs_filename,
                    "--branch-counts", "--branch-probabilities",
                    "--preserve-paths", "--object-directory", dirname]

        self.verbose = verbose

        # NB: Currently, we will only parse English output
        self.env = dict(os.environ)
        self.env['LC_ALL'] = 'en_US'

    def execute(self):
        if self.verbose:
            sys.stdout.write("Running gcov: '%s' in '%s'\n"
                             % (' '.join(self.cmd), os.getcwd()))
        gcov_process = subprocess.Popen(self.cmd, env=self.env,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        (out, err) = gcov_process.communicate()
        if gcov_process.returncode != 0:
            error_msg = ["(ERROR) GCOV returned %d on file %s!"
                         % (gcov_process.returncode, self.filename),
                         "\n    ".join(["GCOV says:"] + err.split('\n'))]
            error_msg = "\n".join(error_msg)
            raise GcovError(error_msg, self.filename)

        return (out.decode('utf-8'), err.decode('utf-8'))


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
    #
    # Launch gcov
    #
    abs_filename = os.path.abspath(filename)

    errors = []
    Done = False

    gcov = Gcov(options.gcov_cmd, abs_filename, options.verbose)

    potential_wd = find_potential_wd(options.objdir, abs_filename)
    while len(potential_wd) > 0 and not Done:
        # NB: either len(potential_wd) == 1, or all entries are absolute
        # paths, so we don't have to chdir(starting_dir) at every
        # iteration.
        os.chdir(potential_wd.pop(0))

        (out, err) = gcov.execute()

        # find the files that gcov created
        gcov_files = find_gcov_files(options.gcov_filter, options.gcov_exclude,
                                     out, options.verbose)

        if source_re.search(err):
            # gcov tossed errors: try the next potential_wd
            errors.append(err)
        else:
            # Process *.gcov files
            gcov_parser = GcovParser(options.root_dir, options.filter,
                                     options.root_filter, options.exclude,
                                     options.exclude_unreachable_branches,
                                     options.verbose)
            for fname in gcov_files['active']:
                gcov_parser.parse(fname, covdata)
            Done = True

        if not options.keep:
            for group in gcov_files.values():
                for fname in group:
                    if os.path.exists(fname):
                        # Only remove files that actually exist.
                        os.remove(fname)

    if options.delete:
        if not abs_filename.endswith('gcno'):
            os.remove(abs_filename)

    if not Done:
        sys.stderr.write(
            "(WARNING) GCOV produced the following errors processing %s:\n"
            "\t   %s"
            "\t(gcovr could not infer a working directory that resolved it.)\n"
            % (filename, "\t   ".join(errors)))


def process_files(datafiles, options):
    start_dir = os.getcwd()
    covdata = {}
    for file in datafiles:
        process_datafile(file, covdata, options)
    if options.verbose:
        sys.stdout.write("".join(["Gathered coveraged data for ",
                                  str(len(covdata)), " files\n"]))
    os.chdir(start_dir)
    return covdata
