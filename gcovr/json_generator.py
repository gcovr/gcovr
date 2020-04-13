# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2019 the gcovr authors
# This software is distributed under the BSD license.

import json
import os
import sys
import functools

from .utils import (calculate_coverage, Logger, presentable_filename,
                    sort_coverage)
from .coverage import FileCoverage


JSON_FORMAT_VERSION = 0.1
PRETTY_JSON_INDENT = 4

def _write_json_result(gcovr_json_dict, output_file, options):
    r"""helper utility to output json format dictionary to a file/STDOUT """
    write_json = json.dump

    if options.prettyjson:
        write_json = functools.partial(write_json, indent=PRETTY_JSON_INDENT,
                                       separators=(',', ': '), sort_keys=True)
    else:
        write_json = functools.partial(write_json, sort_keys=True)

    if output_file is None:
        write_json(gcovr_json_dict, sys.stdout)
    else:
        with open(output_file, 'w') as output:
            write_json(gcovr_json_dict, output)


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
        gcovr_json_file['file'] = presentable_filename(covdata[no].filename,
                                                       root_filter=options.root_filter)
        gcovr_json_file['lines'] = _json_from_lines(covdata[no].lines)
        gcovr_json_root['files'].append(gcovr_json_file)

    _write_json_result(gcovr_json_root, output_file, options)


#
# Produce gcovr JSON summary report
#
def print_json_summary_report(covdata, output_file, options):

    total_lines = 0
    total_covered = 0

    json_dict = {}
    json_dict['current_working_directory'] = options.root
    json_dict['gcovr/format_version'] = JSON_FORMAT_VERSION
    json_dict['files'] = []

    # Data
    keys = sort_coverage(
        covdata, show_branch=options.show_branch,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)

    def _summarize_file_coverage(coverage):
        filename_str = options.root_filter.sub('', coverage.filename)
        if not coverage.filename.endswith(filename_str):
            # Do no truncation if the filter does not start matching at
            # the beginning of the string
            filename_str = coverage.filename
        filename_str = filename_str.replace('\\', '/')

        if options.show_branch:
            total, cover, percent = coverage.branch_coverage()
            uncovered_lines = coverage.uncovered_branches_str()
        else:
            total, cover, percent = coverage.line_coverage()
            uncovered_lines = coverage.uncovered_lines_str()

        return (filename_str, total, cover, percent, uncovered_lines)

    for key in keys:
        (filename, t, n, percent, uncovered_lines) = _summarize_file_coverage(covdata[key])
        total_lines += t
        total_covered += n
        json_dict['files'].append({
            'file': filename,
            'total': t,
            'covered': n,
            'percent': percent,
        })

    # Footer & summary
    percent = calculate_coverage(total_covered, total_lines, nan_value=None)

    json_dict['total'] = total_lines
    json_dict['covered'] = total_covered
    json_dict['percent'] = percent

    _write_json_result(json_dict, output_file, options)

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
