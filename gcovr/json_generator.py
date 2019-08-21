# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2019 the gcovr authors
# This software is distributed under the BSD license.

import json
import os
import sys
import functools

from .utils import presentable_filename, Logger
from .coverage import FileCoverage


JSON_FORMAT_VERSION = 0.1
PRETTY_JSON_INDENT = 4


#
# Produce gcovr JSON report
#
def print_json_report(covdata, output_file, options):
    r"""produce an JSON report in the format partially
    compatible with gcov JSON output"""

    gcovr_json_root = {}
    gcovr_json_root['gcovr/format_version'] = JSON_FORMAT_VERSION
    gcovr_json_root['files'] = []

    for no in sorted(covdata):
        gcovr_json_file = {}
        gcovr_json_file['file'] = presentable_filename(covdata[no].filename, root_filter=options.root_filter)
        gcovr_json_file['lines'] = _json_from_lines(covdata[no].lines)
        gcovr_json_root['files'].append(gcovr_json_file)

    write_json = json.dump
    if options.prettyjson:
        write_json = functools.partial(write_json, indent=PRETTY_JSON_INDENT)

    if options.output:
        with open(options.output, 'w') as output:
            write_json(gcovr_json_root, output)
    else:
        write_json(gcovr_json_root, sys.stdout)


def _json_from_lines(lines):
    json_lines = [_json_from_line(lines[no]) for no in sorted(lines)]
    return json_lines


def _json_from_line(line):
    json_line = {}
    json_line['branches'] = _json_from_branches(line.branches)
    json_line['count'] = line.count
    json_line['line_number'] = line.lineno
    json_line['gcovr/noncode'] = line.noncode
    return json_line


def _json_from_branches(branches):
    json_branches = [_json_from_branch(branches[no]) for no in sorted(branches)]
    return json_branches


def _json_from_branch(branch):
    json_branch = {}
    json_branch['count'] = branch.count
    json_branch['fallthrough'] = bool(branch.fallthrough)
    json_branch['throw'] = bool(branch.throw)
    return json_branch
