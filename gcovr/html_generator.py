# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
import sys
import time
import datetime
import zlib
import io

from .version import __version__
from .utils import commonpath, sort_coverage


class lazy(object):
    def __init__(self, fn):

        def load():
            result = fn()

            def reuse_value():
                return result

            self.get = reuse_value
            return result

        self.get = load

    def __call__(self):
        return self.get()


# Loading Jinja and preparing the environmen is fairly costly.
# Only do this work if templates are actually used.
# This speeds up text and XML output.
@lazy
def templates():
    from jinja2 import Environment, PackageLoader
    return Environment(
        loader=PackageLoader('gcovr'),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True)


low_color = "LightPink"
medium_color = "#FFFF55"
high_color = "LightGreen"
covered_color = "LightGreen"
uncovered_color = "LightPink"
takenBranch_color = "Green"
notTakenBranch_color = "Red"


def html_escape(s):
    """Escape string for inclusion in a HTML body.

    Does not escape ``'``, ``"``, or ``>``.
    """
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    return s


def calculate_coverage(covered, total, nan_value=0.0):
    return nan_value if total == 0 else round(100.0 * covered / total, 1)


def coverage_to_color(coverage, medium_threshold, high_threshold):
    if coverage is None:
        return 'LightGray'
    elif coverage < medium_threshold:
        return low_color
    elif coverage < high_threshold:
        return medium_color
    else:
        return high_color


#
# Produce an HTML report
#
def print_html_report(covdata, options):
    medium_threshold = options.html_medium_threshold
    high_threshold = options.html_high_threshold
    details = options.html_details
    if options.output is None:
        details = False
    data = {}
    data['HEAD'] = options.html_title
    data['VERSION'] = __version__
    data['TIME'] = str(int(time.time()))
    data['DATE'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data['ROWS'] = []
    data['ENC'] = options.html_encoding
    data['low_color'] = low_color
    data['medium_color'] = medium_color
    data['high_color'] = high_color
    data['COVERAGE_MED'] = medium_threshold
    data['COVERAGE_HIGH'] = high_threshold
    data['CSS'] = templates().get_template('style.css').render(
        low_color=low_color,
        medium_color=medium_color,
        high_color=high_color,
        covered_color=covered_color,
        uncovered_color=uncovered_color,
        takenBranch_color=takenBranch_color,
        notTakenBranch_color=notTakenBranch_color
    )
    data['DIRECTORY'] = ''

    branchTotal = 0
    branchCovered = 0
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=True)
        branchTotal += total
        branchCovered += covered
    data['BRANCHES_EXEC'] = str(branchCovered)
    data['BRANCHES_TOTAL'] = str(branchTotal)
    coverage = calculate_coverage(branchCovered, branchTotal, nan_value=None)
    data['BRANCHES_COVERAGE'] = '-' if coverage is None else str(coverage)
    data['BRANCHES_COLOR'] = coverage_to_color(coverage, medium_threshold, high_threshold)

    lineTotal = 0
    lineCovered = 0
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=False)
        lineTotal += total
        lineCovered += covered
    data['LINES_EXEC'] = str(lineCovered)
    data['LINES_TOTAL'] = str(lineTotal)
    coverage = calculate_coverage(lineCovered, lineTotal)
    data['LINES_COVERAGE'] = str(coverage)
    data['LINES_COLOR'] = coverage_to_color(coverage, medium_threshold, high_threshold)

    # Generate the coverage output (on a per-package basis)
    # source_dirs = set()
    files = []
    dirs = []
    filtered_fname = ''
    keys = sort_coverage(
        covdata, show_branch=False,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)
    for f in keys:
        cdata = covdata[f]
        filtered_fname = options.root_filter.sub('', f)
        files.append(filtered_fname)
        dirs.append(os.path.dirname(filtered_fname) + os.sep)
        cdata._filename = filtered_fname
        if not details:
            cdata._sourcefile = None
        else:
            ttmp = os.path.abspath(options.output).split('.')
            longname = cdata._filename.replace(os.sep, '_')
            longname_hash = ""
            while True:
                if len(ttmp) > 1:
                    cdata._sourcefile = \
                        '.'.join(ttmp[:-1]) + \
                        '.' + longname + longname_hash + \
                        '.' + ttmp[-1]
                else:
                    cdata._sourcefile = \
                        ttmp[0] + '.' + longname + longname_hash + '.html'
                # we add a hash at the end and attempt to shorten the
                # filename if it exceeds common filesystem limitations
                if len(os.path.basename(cdata._sourcefile)) < 256:
                    break
                longname_hash = "_" + hex(zlib.crc32(longname) & 0xffffffff)[2:]
                longname = longname[(len(cdata._sourcefile) - len(longname_hash)):]

    # Define the common root directory, which may differ from options.root
    # when source files share a common prefix.
    if len(files) > 1:
        commondir = commonpath(files)
        if commondir != '':
            data['DIRECTORY'] = commondir
    else:
        dir_, file_ = os.path.split(filtered_fname)
        if dir_ != '':
            data['DIRECTORY'] = dir_ + os.sep

    nrows = 0
    for f in keys:
        cdata = covdata[f]
        class_lines = 0
        class_hits = 0
        class_branches = 0
        class_branch_hits = 0
        for line in sorted(cdata.all_lines):
            hits = cdata.covered.get(line, 0)
            class_lines += 1
            if hits > 0:
                class_hits += 1
            branches = cdata.branches.get(line)
            if branches is None:
                pass
            else:
                b_hits = 0
                for v in branches.values():
                    if v > 0:
                        b_hits += 1
                coverage = 100 * b_hits / len(branches)
                class_branch_hits += b_hits
                class_branches += len(branches)

        lines_covered = calculate_coverage(class_hits, class_lines, nan_value=100.0)
        branches_covered = calculate_coverage(class_branch_hits, class_branches, nan_value=None)

        nrows += 1
        data['ROWS'].append(html_row(
            options, details, cdata._sourcefile, nrows,
            directory=data['DIRECTORY'],
            filename=os.path.relpath(
                os.path.realpath(cdata._filename), data['DIRECTORY']),
            LinesExec=class_hits,
            LinesTotal=class_lines,
            LinesCoverage=lines_covered,
            BranchesExec=class_branch_hits,
            BranchesTotal=class_branches,
            BranchesCoverage=branches_covered
        ))

    if data['DIRECTORY'] == '':
        data['DIRECTORY'] = "."
    data['DIRECTORY'] = data['DIRECTORY'].replace('\\', '/')

    htmlString = templates().get_template('root_page.html').render(**data)

    if options.output is None:
        sys.stdout.write(htmlString + '\n')
    else:
        OUTPUT = io.open(options.output, 'w', encoding=options.html_encoding,
                         errors='xmlcharrefreplace')
        OUTPUT.write(htmlString + '\n')
        OUTPUT.close()

    # Return, if no details are requested
    if not details:
        return

    #
    # Generate an HTML file for every source file
    #
    for f in keys:
        cdata = covdata[f]

        data['FILENAME'] = cdata._filename
        data['ROWS'] = ''

        branchTotal, branchCovered, tmp = cdata.coverage(show_branch=True)
        data['BRANCHES_EXEC'] = str(branchCovered)
        data['BRANCHES_TOTAL'] = str(branchTotal)
        coverage = calculate_coverage(branchCovered, branchTotal, nan_value=None)
        data['BRANCHES_COVERAGE'] = '-' if coverage is None else str(coverage)
        data['BRANCHES_COLOR'] = coverage_to_color(coverage, medium_threshold, high_threshold)

        lineTotal, lineCovered, tmp = cdata.coverage(show_branch=False)
        data['LINES_EXEC'] = str(lineCovered)
        data['LINES_TOTAL'] = str(lineTotal)
        coverage = calculate_coverage(lineCovered, lineTotal)
        data['LINES_COVERAGE'] = str(coverage)
        data['LINES_COLOR'] = coverage_to_color(coverage, medium_threshold, high_threshold)

        data['ROWS'] = []
        currdir = os.getcwd()
        os.chdir(options.root_dir)
        INPUT = io.open(data['FILENAME'], 'r', encoding=options.source_encoding,
                        errors='replace')
        ctr = 1
        for line in INPUT:
            data['ROWS'].append(
                source_row(ctr, line.rstrip(), cdata)
            )
            ctr += 1
        INPUT.close()
        os.chdir(currdir)

        htmlString = templates().get_template('source_page.html').render(**data)
        OUTPUT = io.open(cdata._sourcefile, 'w', encoding=options.html_encoding,
                         errors='xmlcharrefreplace')
        OUTPUT.write(htmlString + '\n')
        OUTPUT.close()


def source_row(lineno, source, cdata):
    kwargs = {}
    kwargs['lineno'] = str(lineno)
    if lineno in cdata.covered:
        kwargs['covclass'] = 'coveredLine'
        kwargs['linebranch'] = ''
        # If line has branches them show them with ticks or crosses
        if lineno in cdata.branches.keys():
            branches = cdata.branches.get(lineno)
            branchcounter = 0
            for branch in branches:
                if branches[branch] > 0:
                    kwargs['linebranch'] += '<span class="takenBranch" title="Branch ' + str(branch) + ' taken ' + str(branches[branch]) + ' times">&check;</span>'
                else:
                    kwargs['linebranch'] += '<span class="notTakenBranch" title="Branch ' + str(branch) + ' not taken">&cross;</span>'
                branchcounter += 1
                # Wrap at 4 branches to avoid too wide column
                if (branchcounter > 0) and ((branchcounter % 4) == 0):
                    kwargs['linebranch'] += '<br/>'
        kwargs['linecount'] = str(cdata.covered.get(lineno, 0))
    elif lineno in cdata.uncovered:
        kwargs['covclass'] = 'uncoveredLine'
        kwargs['linebranch'] = ''
        kwargs['linecount'] = ''
    else:
        kwargs['covclass'] = ''
        kwargs['linebranch'] = ''
        kwargs['linecount'] = ''
    kwargs['source'] = html_escape(source)
    return kwargs


#
# Generate the table row for a single file
#
def html_row(options, details, sourcefile, nrows, **kwargs):
    if details and options.relative_anchors:
        sourcefile = os.path.basename(sourcefile)
    if nrows % 2 == 0:
        kwargs['altstyle'] = 'style="background-color:LightSteelBlue"'
    else:
        kwargs['altstyle'] = ''
    if details:
        kwargs['filename'] = '<a href="%s">%s</a>' % (
            sourcefile, kwargs['filename'].replace('\\', '/')
        )
    kwargs['LinesCoverage'] = round(kwargs['LinesCoverage'], 1)
    # Disable the border if the bar is too short to see the color
    if kwargs['LinesCoverage'] < 1e-7:
        kwargs['BarBorder'] = "border:white; "
    else:
        kwargs['BarBorder'] = ""
    if kwargs['LinesCoverage'] < options.html_medium_threshold:
        kwargs['LinesColor'] = low_color
        kwargs['LinesBar'] = 'red'
    elif kwargs['LinesCoverage'] < options.html_high_threshold:
        kwargs['LinesColor'] = medium_color
        kwargs['LinesBar'] = 'yellow'
    else:
        kwargs['LinesColor'] = high_color
        kwargs['LinesBar'] = 'green'

    kwargs['BranchesColor'] = coverage_to_color(kwargs['BranchesCoverage'], options.html_medium_threshold, options.html_high_threshold)
    kwargs['BranchesCoverage'] = '-' if kwargs['BranchesCoverage'] is None else round(kwargs['BranchesCoverage'], 1)

    return kwargs
