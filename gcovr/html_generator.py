# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import os
import sys
import datetime
import zlib
import io

from .version import __version__
from .utils import commonpath, sort_coverage


class Lazy:
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
@Lazy
def templates():
    from jinja2 import Environment, PackageLoader
    return Environment(
        loader=PackageLoader('gcovr'),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True)


class CssRenderer():

    low_color = "LightPink"
    medium_color = "#FFFF55"
    high_color = "LightGreen"
    covered_color = "LightGreen"
    uncovered_color = "LightPink"
    takenBranch_color = "Green"
    notTakenBranch_color = "Red"

    @staticmethod
    def render(tab_size):
        return templates().get_template('style.css').render(
            low_color=CssRenderer.low_color,
            medium_color=CssRenderer.medium_color,
            high_color=CssRenderer.high_color,
            covered_color=CssRenderer.covered_color,
            uncovered_color=CssRenderer.uncovered_color,
            takenBranch_color=CssRenderer.takenBranch_color,
            notTakenBranch_color=CssRenderer.notTakenBranch_color,
            tab_size=tab_size
        )


def calculate_coverage(covered, total, nan_value=0.0):
    return nan_value if total == 0 else round(100.0 * covered / total, 1)


def coverage_to_class(coverage, medium_threshold, high_threshold):
    if coverage is None:
        return 'coverage-unknown'
    if coverage == 0:
        return 'coverage-none'
    if coverage < medium_threshold:
        return 'coverage-low'
    if coverage < high_threshold:
        return 'coverage-medium'
    return 'coverage-high'


class RootInfo:

    def __init__(self, options):
        self.medium_threshold = options.html_medium_threshold
        self.high_threshold = options.html_high_threshold
        self.details = options.html_details
        self.relative_anchors = options.relative_anchors

        self.version = __version__
        self.head = options.html_title
        self.date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.encoding = options.html_encoding
        self.directory = None
        self.branches = dict()
        self.lines = dict()
        self.files = []

    def set_directory(self, directory):
        self.directory = directory

    def get_directory(self):
        return "." if self.directory == '' else self.directory.replace('\\', '/')

    def calculate_branch_coverage(self, covdata):
        branch_total = 0
        branch_covered = 0
        for key in covdata.keys():
            (total, covered, _percent) = covdata[key].branch_coverage()
            branch_total += total
            branch_covered += covered
        self.branches['exec'] = branch_covered
        self.branches['total'] = branch_total
        coverage = calculate_coverage(branch_covered, branch_total, nan_value=None)
        self.branches['coverage'] = '-' if coverage is None else coverage
        self.branches['class'] = self._coverage_to_class(coverage)

    def calculate_line_coverage(self, covdata):
        line_total = 0
        line_covered = 0
        for key in covdata.keys():
            (total, covered, _percent) = covdata[key].line_coverage()
            line_total += total
            line_covered += covered
        self.lines['exec'] = line_covered
        self.lines['total'] = line_total
        coverage = calculate_coverage(line_covered, line_total)
        self.lines['coverage'] = coverage
        self.lines['class'] = self._coverage_to_class(coverage)

    def add_file(self, cdata, link_report, cdata_fname):
        lines_total, lines_exec, _ = cdata.line_coverage()
        branches_total, branches_exec, _ = cdata.branch_coverage()

        line_coverage = calculate_coverage(
            lines_exec, lines_total, nan_value=100.0)
        branch_coverage = calculate_coverage(
            branches_exec, branches_total, nan_value=None)

        lines = {
            'total': lines_total,
            'exec': lines_exec,
            'coverage': round(line_coverage, 1),
            'class': self._coverage_to_class(line_coverage),
        }

        branches = {
            'total': branches_total,
            'exec': branches_exec,
            'coverage': '-' if branch_coverage is None else round(branch_coverage, 1),
            'class': self._coverage_to_class(branch_coverage),
        }

        display_filename = (
            os.path.relpath(os.path.realpath(cdata_fname), self.directory)
            .replace('\\', '/'))

        if link_report is not None:
            if self.relative_anchors:
                link_report = os.path.basename(link_report)

        self.files.append(dict(
            directory=self.directory,
            filename=display_filename,
            link=link_report,
            lines=lines,
            branches=branches,
        ))

    def _coverage_to_class(self, coverage):
        return coverage_to_class(coverage, self.medium_threshold, self.high_threshold)


#
# Produce an HTML report
#
def print_html_report(covdata, output_file, options):
    medium_threshold = options.html_medium_threshold
    high_threshold = options.html_high_threshold
    tab_size = options.html_tab_size
    data = {}
    root_info = RootInfo(options)
    data['info'] = root_info

    data['COVERAGE_MED'] = medium_threshold
    data['COVERAGE_HIGH'] = high_threshold

    self_contained = options.html_self_contained
    if self_contained is None:
        self_contained = not options.html_details

    if self_contained:
        data['css'] = CssRenderer.render(tab_size)
    else:
        css_output = os.path.splitext(output_file)[0] + '.css'
        with open(css_output, 'w') as f:
            f.write(CssRenderer.render(tab_size))

        if options.relative_anchors:
            css_link = os.path.basename(css_output)
        else:
            css_link = css_output
        data['css_link'] = css_link

    root_info.calculate_branch_coverage(covdata)
    root_info.calculate_line_coverage(covdata)

    # Generate the coverage output (on a per-package basis)
    # source_dirs = set()
    files = []
    dirs = []
    filtered_fname = ''
    keys = sort_coverage(
        covdata, show_branch=False,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)
    cdata_fname = {}
    cdata_sourcefile = {}
    for f in keys:
        cdata = covdata[f]
        filtered_fname = options.root_filter.sub('', f)
        files.append(filtered_fname)
        dirs.append(os.path.dirname(filtered_fname) + os.sep)
        cdata_fname[f] = filtered_fname
        if not options.html_details:
            cdata_sourcefile[f] = None
        else:
            cdata_sourcefile[f] = _make_short_sourcename(
                output_file, filtered_fname)

    # Define the common root directory, which may differ from options.root
    # when source files share a common prefix.
    root_directory = ''
    if len(files) > 1:
        commondir = commonpath(files)
        if commondir != '':
            root_directory = commondir
    else:
        dir_, _file = os.path.split(filtered_fname)
        if dir_ != '':
            root_directory = dir_ + os.sep

    root_info.set_directory(root_directory)

    for f in keys:
        root_info.add_file(covdata[f], cdata_sourcefile[f], cdata_fname[f])

    html_string = templates().get_template('root_page.html').render(**data)

    if output_file is None:
        sys.stdout.write(html_string + '\n')
    else:
        with io.open(output_file, 'w', encoding=options.html_encoding,
                     errors='xmlcharrefreplace') as fh:
            fh.write(html_string + '\n')

    # Return, if no details are requested
    if not options.html_details:
        return

    #
    # Generate an HTML file for every source file
    #
    for f in keys:
        cdata = covdata[f]

        data['filename'] = cdata_fname[f]

        branches = dict()
        data['branches'] = branches

        branches['total'], branches['exec'], branches['coverage'] = cdata.branch_coverage()
        branches['class'] = coverage_to_class(branches['coverage'], medium_threshold, high_threshold)
        branches['coverage'] = '-' if branches['coverage'] is None else branches['coverage']

        lines = dict()
        data['lines'] = lines
        lines['total'], lines['exec'], lines['coverage'] = cdata.line_coverage()
        lines['class'] = coverage_to_class(lines['coverage'], medium_threshold, high_threshold)

        data['source_lines'] = []
        currdir = os.getcwd()
        os.chdir(options.root_dir)
        with io.open(data['filename'], 'r', encoding=options.source_encoding,
                     errors='replace') as source_file:
            for ctr, line in enumerate(source_file, 1):
                data['source_lines'].append(
                    source_row(ctr, line.rstrip(), cdata.lines.get(ctr))
                )
        os.chdir(currdir)

        html_string = templates().get_template('source_page.html').render(**data)
        with io.open(cdata_sourcefile[f], 'w', encoding=options.html_encoding,
                     errors='xmlcharrefreplace') as fh:
            fh.write(html_string + '\n')


def source_row(lineno, source, line_cov):
    linebranch = None
    linecount = ''
    covclass = ''
    if line_cov:
        if line_cov.is_covered:
            covclass = 'coveredLine'
            linebranch = source_row_branch(line_cov.branches)
            linecount = line_cov.count
        elif line_cov.is_uncovered:
            covclass = 'uncoveredLine'
    return {
        'lineno': lineno,
        'source': source,
        'covclass': covclass,
        'linebranch': linebranch,
        'linecount': linecount,
    }


def source_row_branch(branches):
    if not branches:
        return None

    taken = 0
    total = 0
    items = []

    for branch_id in sorted(branches):
        branch = branches[branch_id]
        if branch.is_covered:
            taken += 1
        total += 1
        items.append({
            'taken': branch.is_covered,
            'name': branch_id,
            'count': branch.count,
        })

    return {
        'taken': taken,
        'total': total,
        'branches': items,
    }


def _make_short_sourcename(output_file, filename):
    # type: (str, str) -> str
    r"""Make a short-ish file path for --html-detail output.

    Args:
        output_file (str): The --output path.
        filename (str): Path from root to source code.
    """

    output_file_parts = os.path.abspath(output_file).split('.')
    if len(output_file_parts) > 1:
        output_prefix = '.'.join(output_file_parts[:-1])
        output_suffix = output_file_parts[-1]
    else:
        output_prefix = output_file
        output_suffix = 'html'

    longname = filename.replace(os.sep, '_')
    longname_hash = ""
    while True:
        sourcename = '.'.join((
            output_prefix, longname + longname_hash, output_suffix))
        # we add a hash at the end and attempt to shorten the
        # filename if it exceeds common filesystem limitations
        if len(os.path.basename(sourcename)) < 256:
            break
        longname_hash = "_" + hex(zlib.crc32(longname) & 0xffffffff)[2:]
        longname = longname[(len(sourcename) - len(longname_hash)):]
    return sourcename
