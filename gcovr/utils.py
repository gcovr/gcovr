# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2019 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

from argparse import ArgumentTypeError
import os
import platform
import re
import sys
from contextlib import contextmanager

if not (platform.system() == 'Windows' and sys.version_info[0] == 2):
    class LoopChecker(object):
        def __init__(self):
            self._seen = set()

        def already_visited(self, path):
            st = os.stat(path)
            key = (st.st_dev, st.st_ino)
            if key in self._seen:
                return True

            self._seen.add(key)
            return False
else:
    class LoopChecker(object):
        def already_visited(self, path):
            return False


def search_file(predicate, path, exclude_dirs):
    """
    Given a search path, recursively descend to find files that satisfy a
    predicate.
    """
    if path is None or path == ".":
        path = os.getcwd()
    elif not os.path.exists(path):
        raise IOError("Unknown directory '" + path + "'")

    loop_checker = LoopChecker()
    for root, dirs, files in os.walk(os.path.abspath(path), followlinks=True):
        # Check if we've already visited 'root' through the magic of symlinks
        if loop_checker.already_visited(root):
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs
                   if not any(exc.match(os.path.join(root, d))
                              for exc in exclude_dirs)]
        root = os.path.realpath(root)

        for name in files:
            if predicate(name):
                yield os.path.realpath(os.path.join(root, name))


def commonpath(files):
    r"""Find the common prefix of all files.

    This differs from the standard library os.path.commonpath():
     - We first normalize all paths to a realpath.
     - We return a path with a trailing path separator.

    No common path exists under the following circumstances:
     - on Windows when the paths have different drives.
       E.g.: commonpath([r'C:\foo', r'D:\foo']) == ''
     - when the `files` are empty.

    Arguments:
        files (list): the input paths, may be relative or absolute.

    Returns: str
        The common prefix directory as a relative path.
        Always ends with a path separator.
        Returns the empty string if no common path exists.
    """
    if not files:
        return ''

    if len(files) == 1:
        prefix_path = os.path.dirname(os.path.realpath(files[0]))
    else:
        split_paths = [os.path.realpath(path).split(os.path.sep)
                       for path in files]
        # We only have to compare the lexicographically minimum and maximum
        # paths to find the common prefix of all, e.g.:
        #   /a/b/c/d  <- min
        #   /a/b/d
        #   /a/c/a    <- max
        #
        # compare:
        # https://github.com/python/cpython/blob/3.6/Lib/posixpath.py#L487
        min_path = min(split_paths)
        max_path = max(split_paths)
        common = min_path  # assume that min_path is a prefix of max_path
        for i in range(min(len(min_path), len(max_path))):
            if min_path[i] != max_path[i]:
                common = min_path[:i]  # disproven, slice for actual prefix
                break
        prefix_path = os.path.sep.join(common)

    # make the path relative and add a trailing slash
    if prefix_path:
        prefix_path = os.path.join(os.path.relpath(prefix_path), '')
    return prefix_path


#
# Get global statistics
#
def get_global_stats(covdata):
    lines_total = 0
    lines_covered = 0
    branches_total = 0
    branches_covered = 0

    keys = list(covdata.keys())

    for key in keys:
        (total, covered, _) = covdata[key].line_coverage()
        lines_total += total
        lines_covered += covered

        (total, covered, _) = covdata[key].branch_coverage()
        branches_total += total
        branches_covered += covered

    percent = calculate_coverage(lines_covered, lines_total)
    percent_branches = calculate_coverage(branches_covered, branches_total)

    return (lines_total, lines_covered, percent,
            branches_total, branches_covered, percent_branches)


def calculate_coverage(covered, total, nan_value=0.0):
    return nan_value if total == 0 else round(100.0 * covered / total, 1)


class FilterOption(object):
    def __init__(self, regex, path_context=None):
        self.regex = regex
        self.path_context = path_context

    def build_filter(self, logger):
        # Try to detect unintended backslashes and warn.
        # Later, the regex engine may or may not raise a syntax error.
        # An unintended backslash is a literal backslash r"\\",
        # or a regex escape that doesn't exist.
        (suggestion, bs_count) = re.subn(
            r'\\\\|\\(?=[^\WabfnrtuUvx0-9AbBdDsSwWZ])', '/', self.regex)
        if bs_count:
            logger.warn("filters must use forward slashes as path separators")
            logger.warn("your filter : {}", self.regex)
            logger.warn("did you mean: {}", suggestion)

        if os.path.isabs(self.regex):
            return AbsoluteFilter(self.regex)
        else:
            path_context = (self.path_context if self.path_context is not None
                            else os.getcwd())
            return RelativeFilter(path_context, self.regex)


class NonEmptyFilterOption(FilterOption):
    def __init__(self, regex, path_context=None):
        if not regex:
            raise ArgumentTypeError("filter cannot be empty")
        super(NonEmptyFilterOption, self).__init__(regex, path_context)


FilterOption.NonEmpty = NonEmptyFilterOption


class Filter(object):
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def match(self, path):
        os_independent_path = path.replace(os.path.sep, '/')
        return self.pattern.match(os_independent_path)

    def __str__(self):
        return "{name}({pattern})".format(
            name=type(self).__name__, pattern=self.pattern.pattern)


class AbsoluteFilter(Filter):
    def match(self, path):
        abspath = os.path.realpath(path)
        return super(AbsoluteFilter, self).match(abspath)


class RelativeFilter(Filter):
    def __init__(self, root, pattern):
        super(RelativeFilter, self).__init__(pattern)
        self.root = root

    def match(self, path):
        abspath = os.path.realpath(path)
        relpath = os.path.relpath(abspath, self.root)
        return super(RelativeFilter, self).match(relpath)

    def __str__(self):
        return "RelativeFilter({} root={})".format(
            self.pattern.pattern, self.root)


class AlwaysMatchFilter(Filter):
    def __init__(self):
        super(AlwaysMatchFilter, self).__init__("")

    def match(self, path):
        return True


class DirectoryPrefixFilter(Filter):
    def __init__(self, directory):
        abspath = os.path.realpath(directory)
        os_independent_dir = abspath.replace(os.path.sep, '/')
        pattern = re.escape(os_independent_dir + '/')
        super(DirectoryPrefixFilter, self).__init__(pattern)

    def match(self, path):
        normpath = os.path.normpath(path)
        return super(DirectoryPrefixFilter, self).match(normpath)


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

    def error(self, pattern, *args, **kwargs):
        """Write a formatted error to STDERR.

        pattern: a str.format pattern
        args, kwargs: str.format parameters
        """
        pattern = "(ERROR) " + pattern + "\n"
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


def sort_coverage(covdata, show_branch,
                  by_num_uncovered=False, by_percent_uncovered=False):
    """Sort a coverage dict.

    covdata (dict): the coverage dictionary
    show_branch (bool): select branch coverage (True) or line coverage (False)
    by_num_uncovered, by_percent_uncovered (bool):
        select the sort mode. By default, sort alphabetically.

    returns: the sorted keys
    """
    def num_uncovered_key(key):
        cov = covdata[key]
        (total, covered, _) = \
            cov.branch_coverage() if show_branch else cov.line_coverage()
        uncovered = total - covered
        return uncovered

    def percent_uncovered_key(key):
        cov = covdata[key]
        (total, covered, _) = \
            cov.branch_coverage() if show_branch else cov.line_coverage()
        if covered:
            return -1.0 * covered / total
        elif total:
            return total
        else:
            return 1e6

    if by_num_uncovered:
        key_fn = num_uncovered_key
    elif by_percent_uncovered:
        key_fn = percent_uncovered_key
    else:
        key_fn = None  # default key, sort alphabetically

    return sorted(covdata, key=key_fn)


@contextmanager
def open_binary_for_writing(filename=None):
    """Context manager to open and close a file for binary writing.

    Stdout is used if `filename` is None or '-'.
    """
    if filename and filename != '-':
        # files in write binary mode for UTF-8
        fh = open(filename, 'wb')
        close = True
    elif (sys.version_info > (3, 0)):
        # python 3 wants stdout.buffer for binary output
        fh = sys.stdout.buffer
        close = False
    else:
        # python2 doesn't care as much, no stdout.buffer
        fh = sys.stdout
        close = False

    try:
        yield fh
    finally:
        if close:
            fh.close()


def presentable_filename(filename, root_filter):
    # type: (str, re.Regex) -> str
    """mangle a filename so that it is suitable for a report"""

    normalized = root_filter.sub('', filename)
    if filename.endswith(normalized):
        # remove any slashes between the removed prefix and the normalized name
        if filename != normalized:
            while normalized.startswith(os.path.sep):
                normalized = normalized[len(os.path.sep):]
    else:
        # Do no truncation if the filter does not start matching
        # at the beginning of the string
        normalized = filename

    return normalized.replace('\\', '/')
