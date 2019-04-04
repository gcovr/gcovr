# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2019 the gcovr authors
# This software is distributed under the BSD license.

import json
import sys

from .utils import calculate_coverage, sort_coverage

PRETTY_JSON_INDENT = 4
FORMAT_VERSION = 0.1

#
# Produce gcovr json report
#
def print_json_report(covdata, options):
    if options.output:
        OUTPUT = open(options.output, 'w')
    else:
        OUTPUT = sys.stdout
    total_lines = 0
    total_covered = 0

    json_dict = {}
    json_dict['current_working_directory'] = options.root
    json_dict['format_version'] = FORMAT_VERSION
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
        }

    # Footer & summary
    percent = calculate_coverage(total_covered, total_lines, nan_value=None)

    json_dict['total'] = total_lines
    json_dict['covered'] = total_covered
    json_dict['percent'] = percent

    if options.json_summary_pretty:
        json_str = json.dumps(json_dict, indent=PRETTY_JSON_INDENT)
    else:
        json_str = json.dumps(json_dict)
    OUTPUT.write(json_str)

    # Close logfile
    if options.output:
        OUTPUT.close()
