# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
import re
import sys

# iZip is only available in 2.x
try:
    from itertools import izip as zip
except ImportError:
    pass


def link_walker(path, exclude_dirs):
    for root, dirs, files in os.walk(os.path.abspath(path), followlinks=True):
        dirs[:] = [d for d in dirs
                   if not any(exc.match(os.path.join(root, d))
                              for exc in exclude_dirs)]
        yield (os.path.realpath(root), dirs, files)


def search_file(expr, path, exclude_dirs):
    """
    Given a search path, recursively descend to find files that match a
    regular expression.
    """
    ans = []
    pattern = re.compile(expr)
    if path is None or path == ".":
        path = os.getcwd()
    elif not os.path.exists(path):
        raise IOError("Unknown directory '" + path + "'")
    for root, _, files in link_walker(path, exclude_dirs):
        for name in files:
            if pattern.match(name):
                name = os.path.join(root, name)
                ans.append(os.path.realpath(name))
    return ans


def commonpath(files):
    if len(files) == 1:
        return os.path.join(os.path.relpath(os.path.split(files[0])[0]), '')

    common_path = os.path.realpath(files[0])
    common_dirs = common_path.split(os.path.sep)

    for filepath in files[1:]:
        path = os.path.realpath(filepath)
        dirs = path.split(os.path.sep)
        common = []
        for a, b in zip(dirs, common_dirs):
            if a == b:
                common.append(a)
            elif common:
                common_dirs = common
                break
            else:
                return ''

    return os.path.join(os.path.relpath(os.path.sep.join(common_dirs)), '')


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
        (total, covered, _) = covdata[key].coverage(show_branch=False)
        lines_total += total
        lines_covered += covered

        (total, covered, _) = covdata[key].coverage(show_branch=True)
        branches_total += total
        branches_covered += covered

    percent = calculate_coverage(lines_covered, lines_total)
    percent_branches = calculate_coverage(branches_covered, branches_total)

    return (lines_total, lines_covered, percent,
            branches_total, branches_covered, percent_branches)


def calculate_coverage(covered, total, nan_value=0.0):
    return nan_value if total == 0 else round(100.0 * covered / total, 1)


def build_filter(logger, regex):
    # Try to detect unintended backslashes and warn.
    # Later, the regex engine may or may not raise a syntax error.
    # An unintended backslash is a literal backslash r"\\",
    # or a regex escape that doesn't exist.
    (suggestion, bs_count) = re.subn(
        r'\\\\|\\(?=[^\WabfnrtuUvx0-9AbBdDsSwWZ])', '/', regex)
    if bs_count:
        logger.warn("filters must use forward slashes as path separators")
        logger.warn("your filter : {}", regex)
        logger.warn("did you mean: {}", suggestion)

    if os.path.isabs(regex):
        return AbsoluteFilter(regex)
    else:
        return RelativeFilter(os.getcwd(), regex)


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
        os_independent_dir = directory.replace(os.path.sep, '/')
        pattern = re.escape(os_independent_dir + '/')
        super(DirectoryPrefixFilter, self).__init__(pattern)


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
        (total, covered, _) = covdata[key].coverage(show_branch)
        uncovered = total - covered
        return uncovered

    def percent_uncovered_key(key):
        (total, covered, _) = covdata[key].coverage(show_branch)
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
