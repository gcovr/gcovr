# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.1, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import logging
import os
import hashlib
import io
from argparse import ArgumentTypeError

from ..version import __version__
from ..utils import (
    realpath,
    commonpath,
    sort_coverage,
    open_text_for_writing,
)
from ..coverage import CovData, calculate_coverage

logger = logging.getLogger("gcovr")


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
        loader=PackageLoader("gcovr"),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


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
        lstrip_blocks=True,
    )


class CssRenderer:

    Themes = {
        "green": {
            "unknown_color": "LightGray",
            "low_color": "#FF6666",
            "medium_color": "#F9FD63",
            "high_color": "#85E485",
            "covered_color": "#85E485",
            "uncovered_color": "#FF8C8C",
            "excluded_color": "#53BFFD",
            "warning_color": "orangered",
            "takenBranch_color": "Green",
            "notTakenBranch_color": "Red",
            "takenDecision_color": "Green",
            "uncheckedDecision_color": "DarkOrange",
            "notTakenDecision_color": "Red",
        },
        "blue": {
            "unknown_color": "LightGray",
            "low_color": "#FF6666",
            "medium_color": "#F9FD63",
            "high_color": "#66B4FF",
            "covered_color": "#66B4FF",
            "uncovered_color": "#FF8C8C",
            "excluded_color": "#53BFFD",
            "warning_color": "orangered",
            "takenBranch_color": "Blue",
            "notTakenBranch_color": "Red",
            "takenDecision_color": "Green",
            "uncheckedDecision_color": "DarkOrange",
            "notTakenDecision_color": "Red",
        },
    }

    @staticmethod
    def get_themes():
        return list(CssRenderer.Themes.keys())

    @staticmethod
    def get_default_theme():
        return "green"

    @staticmethod
    def render(options):
        template = None
        if options.html_css is not None:
            template = user_templates().get_template(os.path.relpath(options.html_css))
        else:
            template = templates().get_template("style.css")
        return template.render(
            CssRenderer.Themes[options.html_theme], tab_size=options.html_tab_size
        )


class NullHighlighting:
    def get_css(self):
        return ""

    @staticmethod
    def highlighter_for_file(filename):
        return lambda code: [line.rstrip() for line in code.split("\n")]


class PygmentHighlighting:
    def __init__(self):
        self.formatter = None
        try:
            from pygments.formatters.html import HtmlFormatter

            self.formatter = HtmlFormatter(nowrap=True)
        except ImportError as e:  # pragma: no cover
            logger.warning(f"No syntax highlighting available: {str(e)}")

    def get_css(self):
        if self.formatter is None:  # pragma: no cover
            return ""
        return (
            "\n\n/* pygments syntax highlighting */\n" + self.formatter.get_style_defs()
        )

    # Set the lexer for the given filename. Return true if a lexer is found
    def highlighter_for_file(self, filename):
        if self.formatter is None:  # pragma: no cover
            return NullHighlighting.highlighter_for_file(filename)

        import pygments
        from pygments.lexers import get_lexer_for_filename
        from markupsafe import Markup

        try:
            lexer = get_lexer_for_filename(filename, None, stripnl=False)
            return lambda code: [
                Markup(line.rstrip())
                for line in pygments.highlight(code, lexer, self.formatter).split("\n")
            ]
        except pygments.util.ClassNotFound:  # pragma: no cover
            return NullHighlighting.highlighter_for_file(filename)


@Lazy
def get_formatter(options):
    return (
        PygmentHighlighting()
        if options.html_details_syntax_highlighting
        else NullHighlighting()
    )


def coverage_to_class(coverage, medium_threshold, high_threshold):
    if coverage is None:
        return "coverage-unknown"
    if coverage == 0:
        return "coverage-none"
    if coverage < medium_threshold:
        return "coverage-low"
    if coverage < high_threshold:
        return "coverage-medium"
    return "coverage-high"


class RootInfo:
    def __init__(self, options):
        self.medium_threshold = options.html_medium_threshold
        self.high_threshold = options.html_high_threshold
        self.details = options.html_details
        self.relative_anchors = options.relative_anchors
        self.root_filter = options.root_filter

        self.version = __version__
        self.head = options.html_title
        self.date = options.timestamp.isoformat(sep=" ", timespec="seconds")
        self.encoding = options.html_encoding
        self.directory = None
        self.branches = dict()
        self.decisions = dict()
        self.functions = dict()
        self.lines = dict()
        self.files = []
        self.subdirectories = dict()

    def set_directory(self, directory):
        self.directory = directory

    def get_directory(self):
        return "." if self.directory == "" else self.directory.replace("\\", "/")

    def directory_key(self, filename, read_only = False):
        key = os.path.dirname(filename.replace('\\', '/'))
        if self.root_filter.search(key+"/"):
            if not read_only:
                if key not in self.subdirectories:
                    self.subdirectories[key] = {
                        "branch_exec": 0,
                        "branch_total": 0,
                        "branch_percent": 0.0,
                        "lines_exec": 0,
                        "lines_total": 0,
                        "lines_percent": 0.0,
                        "lines_uncovered": 0,
                        "decision_exec": 0,
                        "decision_total": 0,
                        "decision_percent": 0,
                        "decision_uncovered": 0,
                        "function_exec": 0,
                        "function_total": 0,
                        "function_percent": 0,
                        "function_uncovered": 0,
                        "children": set()
                    }
                self.subdirectories[key]["children"].add(filename)
        else:
            key = None
        return key

    def subdirectory_root(self):
        key = next(iter(self.subdirectories))
        while True:
            next_key = self.directory_key(key, read_only=True)
            if not next_key:
                return key
            else:
                key = next_key

    def collapse_subdirectories(self):
        collapse_dirs = set()
        root_key = self.subdirectory_root()
        directory_read_only = True
        for key, value in self.subdirectories.items():
            if len(value["children"]) == 1 and not key == root_key:
                while True:
                    parent_key = self.directory_key(key, read_only=True)
                    if parent_key not in collapse_dirs or parent_key == root_key:
                        break
                if parent_key:
                    self.subdirectories[parent_key]["children"].remove(key)
                    self.subdirectories[parent_key]["children"].add(value["children"].pop())
                    collapse_dirs.add(key)
        for key in collapse_dirs:
            del self.subdirectories[key]

    def add_directory_branch_coverage(self, filename, total, covered):
        key = self.directory_key(filename)
        if key:
            self.subdirectories[key]["branch_exec"] += covered
            self.subdirectories[key]["branch_total"] += total
            self.add_directory_branch_coverage(key, total, covered)

    def add_directory_line_coverage(self, filename, total, covered):
        key = self.directory_key(filename)
        if key:
            self.subdirectories[key]["lines_exec"] += covered
            self.subdirectories[key]["lines_total"] += total
            self.subdirectories[key]["lines_uncovered"] += total - covered
            self.add_directory_line_coverage(key, total, covered)

    def add_directory_decision_coverage(self, filename, total, covered):
        key = self.directory_key(filename)
        if key:
            self.subdirectories[key]["decision_exec"] += covered
            self.subdirectories[key]["decision_total"] += total
            self.subdirectories[key]["decision_uncovered"] += total - covered
            self.add_directory_decision_coverage(key, total, covered)

    def add_directory_function_coverage(self, filename, total, covered):
        key = self.directory_key(filename)
        if key:
            self.subdirectories[key]["function_exec"] += covered
            self.subdirectories[key]["function_total"] += total
            self.subdirectories[key]["function_uncovered"] += total - covered
            self.add_directory_function_coverage(key, total, covered)

    def calculate_branch_coverage(self, covdata: CovData):
        branch_total = 0
        branch_covered = 0
        for key in covdata.keys():
            (total, covered, _percent) = covdata[key].branch_coverage().to_tuple
            branch_total += total
            branch_covered += covered
            self.add_directory_branch_coverage(key, total, covered)
        self.branches["exec"] = branch_covered
        self.branches["total"] = branch_total
        coverage = calculate_coverage(branch_covered, branch_total, nan_value=None)
        self.branches["coverage"] = "-" if coverage is None else coverage
        self.branches["class"] = self._coverage_to_class(coverage)

    def calculate_decision_coverage(self, covdata: CovData):
        decision_total = 0
        decision_covered = 0
        decision_unchecked = 0
        for key in covdata.keys():
            (total, covered, unchecked, _percent) = (
                covdata[key].decision_coverage().to_tuple
            )
            decision_total += total
            decision_covered += covered
            decision_unchecked += unchecked
            self.add_directory_decision_coverage(key, total, covered)
        self.decisions["exec"] = decision_covered
        self.decisions["unchecked"] = decision_unchecked
        self.decisions["total"] = decision_total
        coverage = calculate_coverage(decision_covered, decision_total, nan_value=None)
        self.decisions["coverage"] = "-" if coverage is None else coverage
        self.decisions["class"] = self._coverage_to_class(coverage)

    def calculate_function_coverage(self, covdata: CovData):
        function_total = 0
        function_covered = 0
        for key in covdata.keys():
            (total, covered, _percent) = covdata[key].function_coverage().to_tuple
            function_total += total
            function_covered += covered
            add_directory_function_coverage(key, total, covered)
        self.functions["exec"] = function_covered
        self.functions["total"] = function_total
        coverage = calculate_coverage(function_covered, function_total, nan_value=None)
        self.functions["coverage"] = "-" if coverage is None else coverage
        self.functions["class"] = self._coverage_to_class(coverage)

    def calculate_line_coverage(self, covdata: CovData):
        line_total = 0
        line_covered = 0
        for key in covdata.keys():
            (total, covered, _percent) = covdata[key].line_coverage().to_tuple
            line_total += total
            line_covered += covered
            self.add_directory_line_coverage(key, total, covered)
        self.lines["exec"] = line_covered
        self.lines["total"] = line_total
        coverage = calculate_coverage(line_covered, line_total)
        self.lines["coverage"] = coverage
        self.lines["class"] = self._coverage_to_class(coverage)

    def calculate_directory_coverage(self):
        for key, value in self.subdirectories.items():
            covered = value["branch_exec"]
            total = value["branch_total"]
            coverage = calculate_coverage(covered, total, nan_value=None)
            self.subdirectories[key]["branch_percent"] = coverage
            self.subdirectories[key]["branch_class"] = self._coverage_to_class(coverage)

            covered = value["lines_exec"]
            total = value["lines_total"]
            coverage = calculate_coverage(covered, total, nan_value=None)
            self.subdirectories[key]["lines_percent"] = coverage
            self.subdirectories[key]["lines_class"] = self._coverage_to_class(coverage)

            covered = value["decision_exec"]
            total = value["decision_total"]
            coverage = calculate_coverage(covered, total, nan_value=None)
            self.subdirectories[key]["decision_percent"] = coverage
            self.subdirectories[key]["decision_class"] = self._coverage_to_class(coverage)

            covered = value["function_exec"]
            total = value["function_total"]
            coverage = calculate_coverage(covered, total, nan_value=None)
            self.subdirectories[key]["function_percent"] = coverage
            self.subdirectories[key]["function_class"] = self._coverage_to_class(coverage)

    def write_subdirectories(self, outputfile):
        import json
        class SetEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, set):
                   return list(obj)
                return json.JSONEncoder.default(self, obj)
        with open_text_for_writing(outputfile) as f:
            json.dump(self.subdirectories, f, indent=2, cls=SetEncoder, sort_keys=True)

    def add_file(self, cdata, link_report, cdata_fname):
        lines_total, lines_exec, _ = cdata.line_coverage().to_tuple
        branches_total, branches_exec, _ = cdata.branch_coverage().to_tuple
        (
            decisions_total,
            decisions_exec,
            decisions_unchecked,
            _,
        ) = cdata.decision_coverage().to_tuple
        functions_total, functions_exec, _ = cdata.function_coverage().to_tuple

        line_coverage = calculate_coverage(lines_exec, lines_total, nan_value=100.0)
        branch_coverage = calculate_coverage(
            branches_exec, branches_total, nan_value=None
        )
        decision_coverage = calculate_coverage(
            decisions_exec, decisions_total, nan_value=None
        )
        function_coverage = calculate_coverage(
            functions_exec, functions_total, nan_value=None
        )

        lines = {
            "total": lines_total,
            "exec": lines_exec,
            "coverage": line_coverage,
            "class": self._coverage_to_class(line_coverage),
        }

        branches = {
            "total": branches_total,
            "exec": branches_exec,
            "coverage": "-" if branch_coverage is None else branch_coverage,
            "class": self._coverage_to_class(branch_coverage),
        }

        decisions = {
            "total": decisions_total,
            "exec": decisions_exec,
            "unchecked": decisions_unchecked,
            "coverage": "-"
            if decision_coverage is None
            else round(decision_coverage, 1),
            "class": self._coverage_to_class(decision_coverage),
        }
        functions = {
            "total": functions_total,
            "exec": functions_exec,
            "coverage": "-" if function_coverage is None else function_coverage,
            "class": self._coverage_to_class(function_coverage),
        }

        display_filename = os.path.relpath(
            realpath(cdata_fname), self.directory
        ).replace("\\", "/")

        if link_report is not None:
            if self.relative_anchors:
                link_report = os.path.basename(link_report)

        self.files.append(
            dict(
                directory=self.directory,
                filename=display_filename,
                link=link_report,
                lines=lines,
                branches=branches,
                decisions=decisions,
                functions=functions,
            )
        )

    def _coverage_to_class(self, coverage):
        return coverage_to_class(coverage, self.medium_threshold, self.high_threshold)


#
# Produce an HTML report
#
def print_html_report(covdata: CovData, output_file, options):
    css_data = CssRenderer.render(options)

    data = {}
    root_info = RootInfo(options)
    data["info"] = root_info

    data["SHOW_DECISION"] = root_info.show_decision
    data["COVERAGE_MED"] = root_info.medium_threshold
    data["COVERAGE_HIGH"] = root_info.high_threshold

    self_contained = options.html_self_contained
    if self_contained is None:
        self_contained = not options.html_details
    if output_file == "-":
        if not self_contained:
            raise ArgumentTypeError(
                "Only self contained reports can be printed to STDOUT"
            )
        elif options.html_details:
            raise ArgumentTypeError("Detailed reports can not be printed to STDOUT")

    if output_file.endswith(os.sep):
        output_file += (
            "coverage_details.html" if options.html_details else "coverage.html"
        )

    formatter = get_formatter(options)
    css_data += formatter.get_css()

    if self_contained:
        data["css"] = css_data
    else:
        css_output = os.path.splitext(output_file)[0] + ".css"
        with open_text_for_writing(css_output) as f:
            f.write(css_data)

        if options.relative_anchors:
            css_link = os.path.basename(css_output)
        else:
            css_link = css_output
        data["css_link"] = css_link

    # These steps also add information about subdirectory hierarchy
    root_info.calculate_branch_coverage(covdata)
    root_info.calculate_decision_coverage(covdata)
    root_info.calculate_function_coverage(covdata)
    root_info.calculate_line_coverage(covdata)
    root_info.collapse_subdirectories()

    # Generate the coverage output (on a per-package basis)
    # source_dirs = set()
    files = []
    filtered_fname = ""
    cdata_fname = {}
    cdata_sourcefile = {}
    for f in list(covdata.keys()) + list(root_info.subdirectories.keys()):
        filtered_fname = options.root_filter.sub("", f)
        files.append(filtered_fname)
        cdata_fname[f] = filtered_fname
        if options.html_details:
            cdata_sourcefile[f] = _make_short_sourcename(output_file, filtered_fname)
        else:
            cdata_sourcefile[f] = None

    # Define the common root directory, which may differ from options.root
    # when source files share a common prefix.
    root_directory = ""
    if len(files) > 1:
        commondir = commonpath(files)
        if commondir != "":
            root_directory = commondir
    else:
        dir_, _file = os.path.split(filtered_fname)
        if dir_ != "":
            root_directory = dir_ + os.sep

    root_info.set_directory(root_directory)
    root_info.calculate_directory_coverage()

    sorted_keys = sort_coverage(
        covdata, show_branch=False,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent)
    for f in sorted_keys:
        root_info.add_file(covdata[f], cdata_sourcefile[f], cdata_fname[f])

    if options.html_details:
        (output_prefix, output_suffix) = os.path.splitext(os.path.abspath(output_file))
        if output_suffix == "":
            output_suffix = ".html"
        functions_fname = f"{output_prefix}.functions{output_suffix}"
        data["FUNCTIONS_FNAME"] = os.path.basename(functions_fname)

    if options.html_cascaded_directories:
        write_directory_pages(output_file, covdata, cdata_fname, cdata_sourcefile, options, root_info, data)
    else:
        write_root_page(output_file, options, data)

    # Return, if no details are requested
    if not options.html_details:
        return

    write_source_pages(covdata, cdata_fname, cdata_sourcefile, options, root_info, data)


#
# Generate the HTML file as a flat list for all rows.
#
def write_root_page(output_file, options, data):
    html_string = templates().get_template("root_page.html").render(**data)
    with open_text_for_writing(output_file, encoding=options.html_encoding,
                               errors="xmlcharrefreplace") as fh:
        fh.write(html_string + "\n")


#
# Generate an HTML file for every source file
#
def write_source_pages(covdata, cdata_fname, cdata_sourcefile, options, root_info, data):
    logger = Logger(options.verbose)
    formatter = get_formatter(options)

    error_occurred = False
    all_functions = dict()
    for f, cdata in covdata.items():
        data["filename"] = cdata_fname[f]

        # Only use demangled names (containing a brace)
        data["function_list"] = []
        for name in sorted(cdata.functions.keys()):
            fcdata = cdata.functions[name]
            fdata = dict()
            fdata["name"] = name
            fdata["filename"] = cdata_fname[f]
            fdata["html_filename"] = os.path.basename(cdata_sourcefile[f])
            fdata["line"] = fcdata.lineno
            fdata["count"] = fcdata.count

            data["function_list"].append(fdata)
            all_functions[(fdata["name"], fdata["filename"])] = fdata

        functions = dict()
        data["functions"] = functions
        (
            functions["total"],
            functions["exec"],
            functions["coverage"],
        ) = cdata.function_coverage().to_tuple
        functions["class"] = coverage_to_class(
            functions["coverage"],
            root_info.medium_threshold,
            root_info.high_threshold
        )
        functions["coverage"] = (
            "-" if functions["coverage"] is None else functions["coverage"]
        )

        branches = dict()
        data["branches"] = branches
        (
            branches["total"],
            branches["exec"],
            branches["coverage"],
        ) = cdata.branch_coverage().to_tuple
        branches["class"] = coverage_to_class(
            branches["coverage"],
            root_info.medium_threshold,
            root_info.high_threshold
        )
        branches["coverage"] = (
            "-" if branches["coverage"] is None else branches["coverage"]
        )

        decisions = dict()
        data["decisions"] = decisions
        (
            decisions["total"],
            decisions["exec"],
            decisions["unchecked"],
            decisions["coverage"],
        ) = cdata.decision_coverage().to_tuple
        decisions["class"] = coverage_to_class(
            decisions["coverage"],
            root_info.medium_threshold,
            root_info.high_threshold
        )
        decisions["coverage"] = (
            "-" if decisions["coverage"] is None else decisions["coverage"]
        )

        lines = dict()
        data["lines"] = lines
        (
            lines["total"],
            lines["exec"],
            lines["coverage"],
        ) = cdata.line_coverage().to_tuple
        lines["class"] = coverage_to_class(
            lines["coverage"],
            root_info.medium_threshold,
            root_info.high_threshold
        )

        data["source_lines"] = []
        currdir = os.getcwd()
        os.chdir(options.root_dir)
        max_line_from_cdata = max(cdata.lines.keys(), default=0)
        try:
            with io.open(
                data["filename"],
                "r",
                encoding=options.source_encoding,
                errors="replace",
            ) as source_file:
                lines = formatter.highlighter_for_file(data["filename"])(
                    source_file.read()
                )
                for ctr, line in enumerate(lines, 1):
                    data["source_lines"].append(
                        source_row(ctr, line, cdata.lines.get(ctr))
                    )
                if ctr < max_line_from_cdata:
                    logger.warning(
                        f"File {data['filename']} has {ctr} line(s) but coverage data has {max_line_from_cdata} line(s)."
                    )
        except IOError as e:
            logger.warning(f'File {data["filename"]} not found: {repr(e)}')
            for ctr in range(1, max_line_from_cdata):
                data["source_lines"].append(
                    source_row(
                        ctr,
                        "!!! File not found !!!" if ctr == 1 else "",
                        cdata.lines.get(ctr),
                    )
                )
            error_occurred = True
        os.chdir(currdir)

        html_string = templates().get_template("source_page.html").render(**data)
        with open_text_for_writing(
            cdata_sourcefile[f],
            encoding=options.html_encoding,
            errors="xmlcharrefreplace",
        ) as fh:
            fh.write(html_string + "\n")

    data["all_functions"] = [all_functions[k] for k in sorted(all_functions)]
    html_string = templates().get_template("functions_page.html").render(**data)
    with open_text_for_writing(
        functions_fname, encoding=options.html_encoding, errors="xmlcharrefreplace"
    ) as fh:
        fh.write(html_string + "\n")

    return error_occurred

def row_sort_keys(options):
    row_sort_key = []
    if options.sort_uncovered:
        row_sort_key.append('lines_uncovered')
    if options.sort_percent:
        row_sort_key.append('lines_percent')
    if not row_sort_key:
        row_sort_key.append('filename')
    return ",".join(row_sort_key)

#
# Generate an HTML file for every subdirectory in the hierarchy.
#
def write_directory_pages(output_file, covdata, cdata_fname, cdata_sourcefile, options, root_info, data):
    data['row_sort_key'] = row_sort_keys(options)
    root_key = root_info.subdirectory_root()
    for f, value in root_info.subdirectories.items():
        data['filename'] = options.root_filter.sub('', f)
        data['subdirectory'] = value
        data['date'] = root_info.date
        data['rows'] = []
        for child in value['children']:
            link = os.path.basename(cdata_sourcefile[child])
            if child in root_info.subdirectories:
                child_data = root_info.subdirectories[child]
                data['rows'].append(dict(
                    filename=cdata_fname[child],
                    link=link,
                    branch_exec=child_data['branch_exec'],
                    branch_total=child_data['branch_total'],
                    branch_percent=child_data['branch_percent'],
                    branch_class=child_data['branch_class'],
                    lines_exec=child_data['lines_exec'],
                    lines_total=child_data['lines_total'],
                    lines_uncovered=child_data['lines_uncovered'],
                    lines_percent=child_data['lines_percent'],
                    lines_class=child_data['lines_class'],
                    decision_exec=child_data['decision_exec'],
                    decision_total=child_data['decision_total'],
                    decision_uncovered=child_data['decision_uncovered'],
                    decision_percent=child_data['decision_percent'],
                    decision_class=child_data['decision_class'],
                    function_exec=child_data['function_exec'],
                    function_total=child_data['function_total'],
                    function_uncovered=child_data['function_uncovered'],
                    function_percent=child_data['function_percent'],
                    function_class=child_data['function_class'],
                    ))
            else:
                branch_total, branch_exec, branch_percent = covdata[child].branch_coverage()
                branch_class = root_info._coverage_to_class(branch_percent)
                lines_total, lines_exec, lines_percent = covdata[child].line_coverage()
                lines_class = root_info._coverage_to_class(lines_percent)
                data['rows'].append(dict(
                    filename=cdata_fname[child],
                    link=link,
                    branch_total=branch_total,
                    branch_exec=branch_exec,
                    branch_percent=branch_percent,
                    branch_class=branch_class,
                    lines_exec=lines_exec,
                    lines_total=lines_total,
                    lines_uncovered=lines_total-lines_exec,
                    lines_percent=lines_percent,
                    lines_class=lines_class,
                    decision_exec=decision_exec,
                    decision_total=decision_total,
                    decision_uncovered=decision_total-decision_exec,
                    decision_percent=decision_percent,
                    decision_class=decision_class,
                    function_exec=function_exec,
                    function_total=function_total,
                    function_uncovered=function_total-function_exec,
                    function_percent=function_percent,
                    function_class=function_class
                    ))
        if options.sort_percent:
            for row in data['rows']:
                if not row["lines_percent"]:
                    row["lines_percent"] = 0.0
        html_string = templates().get_template('directory_page.html').render(**data)
        filename = output_file if f == root_key else cdata_sourcefile[f]
        with open_text_for_writing(filename, encoding=options.html_encoding,
                                   errors='xmlcharrefreplace') as fh:
            fh.write(html_string + '\n')

def source_row(lineno, source, line_cov):
    linebranch = None
    linedecision = None
    linecount = ""
    covclass = ""
    if line_cov:
        if line_cov.is_excluded:
            covclass = "excludedLine"
        elif line_cov.is_covered:
            covclass = "coveredLine"
            linebranch = source_row_branch(line_cov.branches)
            linedecision = source_row_decision(line_cov.decision)
            linecount = line_cov.count
        elif line_cov.is_uncovered:
            covclass = "uncoveredLine"
            linedecision = source_row_decision(line_cov.decision)
    return {
        "lineno": lineno,
        "source": source,
        "covclass": covclass,
        "linebranch": linebranch,
        "linedecision": linedecision,
        "linecount": linecount,
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
        items.append(
            {
                "taken": branch.is_covered,
                "name": branch_id,
                "count": branch.count,
            }
        )

    return {
        "taken": taken,
        "total": total,
        "branches": items,
    }


def source_row_decision(decision):
    if decision is None:
        return None

    items = []

    if decision.is_uncheckable:
        items.append(
            {
                "uncheckable": True,
            }
        )
    elif decision.is_conditional:
        items.append(
            {
                "uncheckable": False,
                "taken": True if decision.count_true > 0 else False,
                "count": decision.count_true,
                "name": "true",
            }
        )
        items.append(
            {
                "uncheckable": False,
                "taken": True if decision.count_false > 0 else False,
                "count": decision.count_false,
                "name": "false",
            }
        )
    elif decision.is_switch:
        items.append(
            {
                "uncheckable": False,
                "taken": True if decision.count > 0 else False,
                "count": decision.count,
                "name": "true",
            }
        )
    else:
        RuntimeError("Unknown decision type")

    return {
        "taken": len([i for i in items if i.get("taken", False)]),
        "uncheckable": len([i for i in items if i["uncheckable"]]),
        "total": len(items),
        "decisions": items,
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
    if output_suffix == "":
        output_suffix = ".html"

    filename = filename.replace(os.sep, "/")
    sourcename = (
        ".".join(
            (
                output_prefix,
                os.path.basename(filename),
                hashlib.md5(filename.encode("utf-8")).hexdigest(),
            )
        )
        + output_suffix
    )
    return sourcename
