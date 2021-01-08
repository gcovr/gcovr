# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2019 the gcovr authors
# This software is distributed under the BSD license.

import json
import os
import functools
from .gcov import apply_filter_include_exclude

from .utils import (get_global_stats, Logger, presentable_filename,
                    sort_coverage, summarize_file_coverage, open_text_for_writing)

from .coverage import FileCoverage


JSON_FORMAT_VERSION = "0.2"
JSON_SUMMARY_FORMAT_VERSION = "0.3"
PRETTY_JSON_INDENT = 4


def _write_json_result(gcovr_json_dict, output_file, default_filename, pretty):
    r"""helper utility to output json format dictionary to a file/STDOUT """
    write_json = json.dump

    if pretty:
        write_json = functools.partial(write_json, indent=PRETTY_JSON_INDENT,
                                       separators=(',', ': '), sort_keys=True)
    else:
        write_json = functools.partial(write_json, sort_keys=True)

    with open_text_for_writing(output_file, default_filename) as fh:
        write_json(gcovr_json_dict, fh)


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

    _write_json_result(gcovr_json_root, output_file, 'coverage.json', options.json_pretty)


#
# Produce gcovr JSON summary report
#
def print_json_summary_report(covdata, output_file, options):

    json_dict = {}

    json_dict['root'] = os.path.relpath(options.root, os.getcwd() if output_file == '-' else output_file)
    json_dict['gcovr/summary_format_version'] = JSON_SUMMARY_FORMAT_VERSION
    json_dict['files'] = []

    # Data
    keys = sort_coverage(
        covdata, show_branch=options.show_branch,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)

    for key in keys:
        file_stats = summarize_file_coverage(covdata[key], options.root_filter)

        json_dict['files'].append({
            'filename': file_stats['filename'],
            'line_total': file_stats['line_total'],
            'line_covered': file_stats['line_covered'],
            'line_percent': file_stats['line_percent'],
            'branch_total': file_stats['branch_total'],
            'branch_covered': file_stats['branch_covered'],
            'branch_covered_percent': file_stats['branch_covered_percent'],
            'branch_executed': file_stats['branch_executed'],
            'branch_executed_percent': file_stats['branch_executed_percent'],
            'call_total': file_stats['call_total'],
            'call_executed': file_stats['call_executed'],
            'call_percent': file_stats['call_percent'],
        })

    global_stats = get_global_stats(covdata)

    # Footer & summary
    json_dict['line_total'] = global_stats['lines_total']
    json_dict['line_covered'] = global_stats['lines_covered']
    json_dict['line_percent'] = global_stats['lines_percent']

    json_dict['branch_total'] = global_stats['branches_total']
    json_dict['branch_covered'] = global_stats['branches_covered']
    json_dict['branch_covered_percent'] = global_stats['branches_covered_percent']
    json_dict['branch_executed'] = global_stats['branches_executed']
    json_dict['branches_executed_percent'] = global_stats['branches_executed_percent']

    json_dict['calls_total'] = global_stats['calls_total']
    json_dict['calls_executed'] = global_stats['calls_executed']
    json_dict['calls_percent'] = global_stats['calls_percent']

    _write_json_result(json_dict, output_file, 'summary_coverage.json', options.json_summary_pretty)


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
            file_path = os.path.join(
                os.path.abspath(options.root),
                os.path.normpath(gcovr_file['file']))

            filtered, excluded = apply_filter_include_exclude(
                file_path, options.filter, options.exclude)

            # Ignore if the filename does not match the filter
            if filtered:
                logger.verbose_msg("  Filtering coverage data for file {}", file_path)
                continue

            # Ignore if the filename matches the exclude pattern
            if excluded:
                logger.verbose_msg("  Excluding coverage data for file {}", file_path)
                continue

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
    json_line['calls'] = _json_from_calls(line.calls)
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
    json_branch['executed'] = bool(branch.executed)
    return json_branch


def _json_from_calls(calls):
    json_calls = [_json_from_call(calls[no]) for no in sorted(calls)]
    return json_calls


def _json_from_call(call):
    json_call = {}
    json_call['count'] = call.count
    return json_call


def _lines_from_json(file, json_lines):
    [_line_from_json(file.line(json_line['line_number']), json_line) for json_line in json_lines]


def _line_from_json(line, json_line):
    line.noncode = json_line['gcovr/noncode']
    line.count = json_line['count']
    _branches_from_json(line, json_line['branches'])
    _calls_from_json(line, json_line['calls'])


def _branches_from_json(line, json_branches):
    [_branch_from_json(line.branch(no), json_branch) for no, json_branch in enumerate(json_branches, 0)]


def _branch_from_json(branch, json_branch):
    branch.fallthrough = json_branch['fallthrough']
    branch.throw = json_branch['throw']
    branch.count = json_branch['count']
    branch.executed = json_branch['executed']


def _calls_from_json(line, json_calls):
    [_call_from_json(line.call(no), json_call) for no, json_call in enumerate(json_calls, 0)]


def _call_from_json(call, json_call):
    call.count = json_call['count']
