# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import os
import datetime
import hashlib
import io
from argparse import ArgumentTypeError

from ..version import __version__
from ..utils import commonpath, sort_coverage, calculate_coverage, Logger, open_text_for_writing


class Lazy:
    def __init__(self, fn):

        def load(*args):
            result = fn(*args)

            def reuse_value(*args):
                return result

            self.get = reuse_value
            return result

        self.get = load

    def __call__(self, *args):
        return self.get(*args)


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


@Lazy
def user_templates():
    from jinja2 import Environment, FunctionLoader

    def load_user_template(template):
        contents = None
        try:
            with open(template, "rb") as f:
                contents = f.read().decode("utf-8")
        # This exception can only occure if the file gets inaccesable while gcovr is running.
        except Exception:  # pragma: no cover
            pass

        return contents

    return Environment(
        loader=FunctionLoader(load_user_template),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True)


class CssRenderer():

    Themes = {
        'green': {
            'unknown_color': "LightGray",
            'low_color': "#FF6666",
            'medium_color': "#F9FD63",
            'high_color': "#85E485",
            'covered_color': "#85E485",
            'uncovered_color': "#FF8C8C",
            'takenBranch_color': "Green",
            'notTakenBranch_color': "Red"
        },
        'blue': {
            'unknown_color': "LightGray",
            'low_color': "#FF6666",
            'medium_color': "#F9FD63",
            'high_color': "#66B4FF",
            'covered_color': "#66B4FF",
            'uncovered_color': "#FF8C8C",
            'takenBranch_color': "Blue",
            'notTakenBranch_color': "Red"
        }
    }

    @staticmethod
    def get_themes():
        return list(CssRenderer.Themes.keys())

    @staticmethod
    def get_default_theme():
        return 'green'

    @staticmethod
    def render(options):
        template = None
        if options.html_css is not None:
            template = user_templates().get_template(os.path.relpath(options.html_css))
        else:
            template = templates().get_template('style.css')
        return template.render(
            CssRenderer.Themes[options.html_theme],
            tab_size=options.html_tab_size
        )


class NullHighlighting:
    def get_css(self):
        return ''

    @staticmethod
    def highlighter_for_file(filename):
        return lambda code: [line.rstrip() for line in code.split("\n")]


class PygmentHighlighting:
    def __init__(self, options):
        self.logger = Logger(options.verbose)
        self.formatter = None
        try:
            from pygments.formatters.html import HtmlFormatter
            self.formatter = HtmlFormatter(nowrap=True)
        except ImportError as e:  # pragma: no cover
            self.logger.warn("No syntax highlighting available: {}".format(str(e)))

    def get_css(self):
        if self.formatter is None:  # pragma: no cover
            return ''
        return "\n\n/* pygments syntax highlighting */\n" + self.formatter.get_style_defs()

    # Set the lexer for the given filename. Return true if a lexer is found
    def highlighter_for_file(self, filename):
        if self.formatter is None:  # pragma: no cover
            return NullHighlighting.highlighter_for_file(filename)

        import pygments
        from pygments.lexers import get_lexer_for_filename
        from jinja2 import Markup
        try:
            lexer = get_lexer_for_filename(filename, None, stripnl=False)
            return lambda code: [Markup(line.rstrip()) for line in pygments.highlight(code, lexer, self.formatter).split("\n")]
        except pygments.util.ClassNotFound:  # pragma: no cover
            return NullHighlighting.highlighter_for_file(filename)


@Lazy
def get_formatter(options):
    return PygmentHighlighting(options) if options.html_details_syntax_highlighting else NullHighlighting()


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
            'coverage': line_coverage,
            'class': self._coverage_to_class(line_coverage),
        }

        branches = {
            'total': branches_total,
            'exec': branches_exec,
            'coverage': '-' if branch_coverage is None else branch_coverage,
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
    logger = Logger(options.verbose)
    css_data = CssRenderer.render(options)
    medium_threshold = options.html_medium_threshold
    high_threshold = options.html_high_threshold

    data = {}
    root_info = RootInfo(options)
    data['info'] = root_info

    data['COVERAGE_MED'] = medium_threshold
    data['COVERAGE_HIGH'] = high_threshold

    self_contained = options.html_self_contained
    if self_contained is None:
        self_contained = not options.html_details
    if output_file == '-':
        if not self_contained:
            raise ArgumentTypeError("Only self contained reports can be printed to STDOUT")
        elif options.html_details:
            raise ArgumentTypeError("Detailed reports can not be printed to STDOUT")

    if output_file.endswith(os.sep):
        output_file += 'coverage_details.html' if options.html_details else 'coverage.html'

    formatter = get_formatter(options)
    css_data += formatter.get_css()

    if self_contained:
        data['css'] = css_data
    else:
        css_output = os.path.splitext(output_file)[0] + '.css'
        with open_text_for_writing(css_output) as f:
            f.write(css_data)

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
        if options.html_details:
            cdata_sourcefile[f] = _make_short_sourcename(
                output_file, filtered_fname)
        else:
            cdata_sourcefile[f] = None

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

    with open_text_for_writing(output_file, encoding=options.html_encoding,
                               errors='xmlcharrefreplace') as fh:
        fh.write(html_string + '\n')

    # Return, if no details are requested
    if not options.html_details:
        return

    #
    # Generate an HTML file for every source file
    #
    error_occurred = False
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
        max_line_from_cdata = max(cdata.lines.keys())
        try:
            with io.open(data['filename'], 'r', encoding=options.source_encoding,
                         errors='replace') as source_file:
                lines = formatter.highlighter_for_file(data['filename'])(source_file.read())
                for ctr, line in enumerate(lines, 1):
                    data['source_lines'].append(
                        source_row(ctr, line, cdata.lines.get(ctr))
                    )
                if ctr < max_line_from_cdata:
                    logger.warn(
                        'File {filename} has {file_lines} line(s) but coverage data has {cdata_lines} line(s).',
                        filename=data['filename'],
                        file_lines=ctr,
                        cdata_lines=max_line_from_cdata
                    )
        except IOError as e:
            logger.warn('File {filename} not found: {reason}', filename=data['filename'], reason=repr(e))
            for ctr in range(1, max_line_from_cdata):
                data['source_lines'].append(
                    source_row(ctr, '!!! File not found !!!' if ctr == 1 else '', cdata.lines.get(ctr))
                )
            error_occurred = True
        os.chdir(currdir)

        html_string = templates().get_template('source_page.html').render(**data)
        with open_text_for_writing(cdata_sourcefile[f], encoding=options.html_encoding,
                                   errors='xmlcharrefreplace') as fh:
            fh.write(html_string + '\n')
    return error_occurred


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
        defaultdefault_filename_name (str): The -default output name.
        filename (str): Path from root to source code.
    """

    (output_prefix, output_suffix) = os.path.splitext(os.path.abspath(output_file))
    if output_suffix == '':
        output_suffix = '.html'

    filename = filename.replace(os.sep, '/')
    sourcename = '.'.join((output_prefix,
                          os.path.basename(filename),
                          hashlib.md5(filename.encode('utf-8')).hexdigest())) + output_suffix
    return sourcename
