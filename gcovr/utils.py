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


def resolve_symlinks(orig_path):
    """
    Return the normalized absolute path name with all symbolic links resolved
    """
    return os.path.realpath(orig_path)
    # WEH - why doesn't os.path.realpath() suffice here?
    #
    drive, tmp = os.path.splitdrive(os.path.abspath(orig_path))
    if not drive:
        drive = os.path.sep
    parts = tmp.split(os.path.sep)
    actual_path = [drive]
    while parts:
        actual_path.append(parts.pop(0))
        if not os.path.islink(os.path.join(*actual_path)):
            continue
        actual_path[-1] = os.readlink(os.path.join(*actual_path))
        tmp_drive, tmp_path = os.path.splitdrive(
            resolve_symlinks(os.path.join(*actual_path)))
        if tmp_drive:
            drive = tmp_drive
        actual_path = [drive] + tmp_path.split(os.path.sep)
    return os.path.join(*actual_path)


#
# Class that creates path aliases
#
class PathAliaser(object):

    def __init__(self):
        self.aliases = {}
        self.master_targets = set()
        self.preferred_name = {}

    def path_startswith(self, path, base):
        return path.startswith(base) and (
            len(base) == len(path) or path[len(base)] == os.path.sep)

    def master_path(self, path):
        match_found = False
        while True:
            for base, alias in self.aliases.items():
                if self.path_startswith(path, base):
                    path = alias + path[len(base):]
                    match_found = True
                    break
            for master_base in self.master_targets:
                if self.path_startswith(path, master_base):
                    return path, master_base, True
            if match_found:
                sys.stderr.write(
                    "(ERROR) violating fundamental assumption while walking "
                    "directory tree.\n\tPlease report this to the gcovr "
                    "developers.\n")
            return path, None, match_found

    def unalias_path(self, path):
        path = resolve_symlinks(path)
        path, master_base, known_path = self.master_path(path)
        if not known_path:
            return path
        # Try and resolve the preferred name for this location
        if master_base in self.preferred_name:
            return self.preferred_name[master_base] + path[len(master_base):]
        return path

    def add_master_target(self, master):
        self.master_targets.add(master)

    def add_alias(self, target, master):
        self.aliases[target] = master

    def set_preferred(self, master, preferred):
        self.preferred_name[master] = preferred


aliases = PathAliaser()


# This is UGLY.  Here's why: UNIX resolves symbolic links by walking the
# entire directory structure.  What that means is that relative links
# are always relative to the actual directory inode, and not the
# "virtual" path that the user might have traversed (over symlinks) on
# the way to that directory.  Here's the canonical example:
#
#   a / b / c / testfile
#   a / d / e --> ../../a/b
#   m / n --> /a
#   x / y / z --> /m/n/d
#
# If we start in "y", we will see the following directory structure:
#   y
#   |-- z
#       |-- e
#           |-- c
#               |-- testfile
#
# The problem is that using a simple traversal based on the Python
# documentation:
#
#    (os.path.join(os.path.dirname(path), os.readlink(result)))
#
# will not work: we will see a link to /m/n/d from /x/y, but completely
# miss the fact that n is itself a link.  If we then naively attempt to
# apply the "c" relative link, we get an intermediate path that looks
# like "/m/n/d/e/../../a/b", which would get normalized to "/m/n/a/b"; a
# nonexistant path.  The solution is that we need to walk the original
# path, along with the full path of all links 1 directory at a time and
# check for embedded symlinks.
#
#
# NB:  Users have complained that this code causes a performance issue.
# I have replaced this logic with os.walk(), which works for Python >= 2.6
#
def link_walker(path, exclude_dirs):
    for root, dirs, files in os.walk(os.path.abspath(path), followlinks=True):
        dirs[:] = [d for d in dirs
                   if not any(exc.match(os.path.join(root, d))
                              for exc in exclude_dirs)]
        yield (os.path.abspath(os.path.realpath(root)), dirs, files)


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
                if os.path.islink(name):
                    ans.append(os.path.abspath(os.readlink(name)))
                else:
                    ans.append(os.path.abspath(name))
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
