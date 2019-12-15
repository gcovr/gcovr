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


class CssRenderer():

    low_color = "LightPink"
    medium_color = "#FFFF55"
    high_color = "LightGreen"
    covered_color = "LightGreen"
    uncovered_color = "LightPink"
    takenBranch_color = "Green"
    notTakenBranch_color = "Red"

    @staticmethod
    def render():
        return templates().get_template('style.css').render(
            low_color=CssRenderer.low_color,
            medium_color=CssRenderer.medium_color,
            high_color=CssRenderer.high_color,
            covered_color=CssRenderer.covered_color,
            uncovered_color=CssRenderer.uncovered_color,
            takenBranch_color=CssRenderer.takenBranch_color,
            notTakenBranch_color=CssRenderer.notTakenBranch_color
        )


def html_escape(s):
    """Escape string for inclusion in a HTML body.

    Does not escape ``'``, ``"``, or ``>``.
    """
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    return s


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


class RootInfo(object):

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

    def set_directory(self, directory):
        self.directory = directory

    def get_directory(self):
        return "." if self.directory == '' else self.directory.replace('\\', '/')

    def calculate_branch_coverage(self, covdata):
        branchTotal = 0
        branchCovered = 0
        for key in covdata.keys():
            (total, covered, percent) = covdata[key].branch_coverage()
            branchTotal += total
            branchCovered += covered
        self.branches['exec'] = str(branchCovered)
        self.branches['total'] = str(branchTotal)
        coverage = calculate_coverage(branchCovered, branchTotal, nan_value=None)
        self.branches['coverage'] = '-' if coverage is None else str(coverage)
        self.branches['class'] = coverage_to_class(coverage, self.medium_threshold, self.high_threshold)
        self.files = []

    def calculate_line_coverage(self, covdata):
        lineTotal = 0
        lineCovered = 0
        for key in covdata.keys():
            (total, covered, percent) = covdata[key].line_coverage()
            lineTotal += total
            lineCovered += covered
        self.lines['exec'] = str(lineCovered)
        self.lines['total'] = str(lineTotal)
        coverage = calculate_coverage(lineCovered, lineTotal)
        self.lines['coverage'] = str(coverage)
        self.lines['class'] = coverage_to_class(coverage, self.medium_threshold, self.high_threshold)

    def add_file(self, cdata, cdata_sourcefile, cdata_fname):
        lines = dict()
        branches = dict()

        lines['total'], lines['exec'], _ = cdata.line_coverage()
        branches['total'], branches['exec'], _ = cdata.branch_coverage()

        lines['coverage'] = calculate_coverage(
            lines['exec'], lines['total'], nan_value=100.0)
        branches['coverage'] = calculate_coverage(
            branches['exec'], branches['total'], nan_value=None)

        self.files.append(self._html_row(
            cdata_sourcefile,
            directory=self.directory,
            filename=os.path.relpath(
                os.path.realpath(cdata_fname), self.directory),
            lines=lines,
            branches=branches
        ))

    def _coverage_to_class(self, coverage):
        return coverage_to_class(coverage, self.medium_threshold, self.high_threshold)

    #
    # Generate the table row for a single file
    #
    def _html_row(self, sourcefile, **kwargs):
        if self.details and self.relative_anchors:
            sourcefile = os.path.basename(sourcefile)
        if self.details:
            kwargs['filename'] = '<a href="{}">{}</a>'.format(
                sourcefile, kwargs['filename'].replace('\\', '/')
            )

        kwargs['lines']['coverage'] = round(kwargs['lines']['coverage'], 1)
        kwargs['lines']['class'] = self._coverage_to_class(kwargs['lines']['coverage'])
        kwargs['lines']['bar'] = self._coverage_to_class(kwargs['lines']['coverage'])

        kwargs['branches']['class'] = self._coverage_to_class(kwargs['branches']['coverage'])
        kwargs['branches']['coverage'] = '-' if kwargs['branches']['coverage'] is None else round(kwargs['branches']['coverage'], 1)

        return kwargs


#
# Produce an HTML report
#
def print_html_report(covdata, output_file, options):
    medium_threshold = options.html_medium_threshold
    high_threshold = options.html_high_threshold
    data = {}
    root_info = RootInfo(options)
    data['info'] = root_info

    data['COVERAGE_MED'] = medium_threshold
    data['COVERAGE_HIGH'] = high_threshold

    data['css'] = CssRenderer.render()

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
        dir_, file_ = os.path.split(filtered_fname)
        if dir_ != '':
            root_directory = dir_ + os.sep

    root_info.set_directory(root_directory)

    for f in keys:
        root_info.add_file(covdata[f], cdata_sourcefile[f], cdata_fname[f])

    htmlString = templates().get_template('root_page.html').render(**data)

    if output_file is None:
        sys.stdout.write(htmlString + '\n')
    else:
        with io.open(output_file, 'w', encoding=options.html_encoding,
                     errors='xmlcharrefreplace') as fh:
            fh.write(htmlString + '\n')

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

        htmlString = templates().get_template('source_page.html').render(**data)
        with io.open(cdata_sourcefile[f], 'w', encoding=options.html_encoding,
                     errors='xmlcharrefreplace') as fh:
            fh.write(htmlString + '\n')


def source_row(lineno, source, line_cov):
    kwargs = {}
    kwargs['lineno'] = str(lineno)
    kwargs['linebranch'] = []
    if line_cov and line_cov.is_covered:
        kwargs['covclass'] = 'coveredLine'
        # If line has branches them show them with ticks or crosses
        branches = line_cov.branches
        branchcounter = 0
        for branch_id in sorted(branches):
            branchcounter += 1
            branch = branches[branch_id]
            branch_args = {}
            if branch.is_covered:
                branch_args['class'] = 'takenBranch'
                branch_args['message'] = 'Branch {name} taken {count} times'.format(
                    name=branch_id, count=branch.count)
                branch_args['symbol'] = '&check;'
            else:
                branch_args['class'] = 'notTakenBranch'
                branch_args['message'] = 'Branch {name} not taken'.format(
                    name=branch_id)
                branch_args['symbol'] = '&cross;'
            branch_args['wrap'] = (branchcounter % 4) == 0
            kwargs['linebranch'].append(branch_args)
        kwargs['linecount'] = str(line_cov.count)
    elif line_cov and line_cov.is_uncovered:
        kwargs['covclass'] = 'uncoveredLine'
        kwargs['linebranch'] = ''
        kwargs['linecount'] = ''
    else:
        kwargs['covclass'] = ''
        kwargs['linebranch'] = ''
        kwargs['linecount'] = ''
    kwargs['source'] = html_escape(source)
    return kwargs


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
