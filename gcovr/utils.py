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
        for exc in exclude_dirs:
            for d in dirs:
                m = exc.search(d)
                if m is not None:
                    dirs[:] = [d for d in dirs if d is not m.group()]
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
    for root, dirs, files in link_walker(path, exclude_dirs):
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

    for f in files[1:]:
        path = os.path.realpath(f)
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
        (t, n, txt) = covdata[key].coverage(show_branch=False)
        lines_total += t
        lines_covered += n

        (t, n, txt) = covdata[key].coverage(show_branch=True)
        branches_total += t
        branches_covered += n

    percent = calculate_coverage(lines_covered, lines_total)
    percent_branches = calculate_coverage(branches_covered, branches_total)

    return (lines_total, lines_covered, percent,
            branches_total, branches_covered, percent_branches)


def calculate_coverage(covered, total, nan_value=0.0):
    return nan_value if total == 0 else round(100.0 * covered / total, 1)


def build_filter(regex):
    if os.name == 'nt':
        # Windows path separators must be escaped before being parsed into a
        # regex, but we do not want to escape the regex itself, so instead of
        # using realpath, we escape the path and join it manually (realpath
        # doesn't resolve symlinks on Windows anyway)
        return re.compile(re.escape(os.getcwd() + "\\") + regex)
    else:
        return re.compile(os.path.realpath(regex))
