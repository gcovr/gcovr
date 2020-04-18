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
        write_json = functools.partial(write_json, indent=PRETTY_JSON_INDENT, separators=(',', ': '), sort_keys=True)
    else:
        write_json = functools.partial(write_json, sort_keys=True)

    if options.output:
        with open(options.output, 'w') as output:
            write_json(gcovr_json_root, output)
    else:
        write_json(gcovr_json_root, sys.stdout)


#
#  Get coverage from already existing gcovr JSON files
#
def gcovr_json_files_to_coverage(filenames, covdata, options):
    r"""merge a coverage from multiple reports in the format
    partially compatible with gcov JSON output"""

    logger = Logger(options.verbose)

    for filename in filenames:
        gcovr_json_data = {}
        logger.verbose_msg("Processing JSON file: {}", filename)

        with open(filename, 'r') as json_file:
            gcovr_json_data = json.load(json_file)

        assert gcovr_json_data['gcovr/format_version'] == JSON_FORMAT_VERSION

        coverage = {}
        for gcovr_file in gcovr_json_data['files']:
            file_path = os.path.join(os.path.abspath(options.root), gcovr_file['file'])
            file_coverage = FileCoverage(file_path)
            _lines_from_json(file_coverage, gcovr_file['lines'])
            coverage[file_path] = file_coverage

        _split_coverage_results(covdata, coverage)


def _split_coverage_results(covdata, coverages):
    for coverage in coverages.values():
        if coverage.filename not in covdata:
            covdata[coverage.filename] = FileCoverage(coverage.filename)

        covdata[coverage.filename].update(coverage)


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


def _lines_from_json(file, json_lines):
    [_line_from_json(file.line(json_line['line_number']), json_line) for json_line in json_lines]


def _line_from_json(line, json_line):
    line.noncode = json_line['gcovr/noncode']
    line.count = json_line['count']
    _branches_from_json(line, json_line['branches'])


def _branches_from_json(line, json_branches):
    [_branch_from_json(line.branch(no), json_branch) for no, json_branch in enumerate(json_branches, 0)]


def _branch_from_json(branch, json_branch):
    branch.fallthrough = json_branch['fallthrough']
    branch.throw = json_branch['throw']
    branch.count = json_branch['count']
