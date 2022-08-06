# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.2, a parsing and reporting tool for gcov.
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
from typing import Callable, Optional, Union

from ..version import __version__
from ..utils import (
    realpath,
    commonpath,
    sort_coverage,
    open_text_for_writing,
)
from ..coverage import (
    CovData,
    CoverageStat,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageStat,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    SummarizedStats,
)

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
        self.medium_threshold_line = options.html_medium_threshold_line
        self.high_threshold_line = options.html_high_threshold_line
        self.medium_threshold_branch = options.html_medium_threshold_branch
        self.high_threshold_branch = options.html_high_threshold_branch
        self.details = options.html_details
        self.relative_anchors = options.relative_anchors

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

    def set_directory(self, directory):
        self.directory = directory

    def get_directory(self):
        return "." if self.directory == "" else self.directory.replace("\\", "/")

    def set_coverage(self, covdata: CovData) -> None:
        """Update this RootInfo with a summary of the CovData."""
        stats = SummarizedStats.from_covdata(covdata)
        self.lines = dict_from_stat(stats.line, self._line_coverage_to_class, 0.0)
        self.functions = dict_from_stat(stats.function, self._coverage_to_class)
        self.branches = dict_from_stat(stats.branch, self._branch_coverage_to_class)
        self.decisions = dict_from_stat(stats.decision, self._coverage_to_class)

    def add_file(self, cdata, link_report, cdata_fname):
        stats = SummarizedStats.from_file(cdata)

        lines = {
            "total": stats.line.total,
            "exec": stats.line.covered,
            "coverage": stats.line.percent_or(100.0),
            "class": self._line_coverage_to_class(stats.line.percent_or(100.0)),
        }

        functions = {
            "total": stats.function.total,
            "exec": stats.function.covered,
            "coverage": stats.function.percent_or("-"),
            "class": self._coverage_to_class(stats.function.percent),
        }

        branches = {
            "total": stats.branch.total,
            "exec": stats.branch.covered,
            "coverage": stats.branch.percent_or("-"),
            "class": self._branch_coverage_to_class(stats.branch.percent),
        }

        decisions = {
            "total": stats.decision.total,
            "exec": stats.decision.covered,
            "unchecked": stats.decision.uncheckable,
            "coverage": stats.decision.percent_or("-"),
            "class": self._coverage_to_class(stats.decision.percent),
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

    def _line_coverage_to_class(self, coverage):
        return coverage_to_class(
            coverage, self.medium_threshold_line, self.high_threshold_line
        )

    def _branch_coverage_to_class(self, coverage):
        return coverage_to_class(
            coverage, self.medium_threshold_branch, self.high_threshold_branch
        )


#
# Produce an HTML report
#
def print_html_report(covdata: CovData, output_file, options):
    css_data = CssRenderer.render(options)
    medium_threshold = options.html_medium_threshold
    high_threshold = options.html_high_threshold
    medium_threshold_line = options.html_medium_threshold_line
    high_threshold_line = options.html_high_threshold_line
    medium_threshold_branch = options.html_medium_threshold_branch
    high_threshold_branch = options.html_high_threshold_branch
    show_decision = options.show_decision

    data = {}
    root_info = RootInfo(options)
    data["info"] = root_info

    data["SHOW_DECISION"] = show_decision
    data["COVERAGE_MED"] = medium_threshold
    data["COVERAGE_HIGH"] = high_threshold
    data["LINE_COVERAGE_MED"] = medium_threshold_line
    data["LINE_COVERAGE_HIGH"] = high_threshold_line
    data["BRANCH_COVERAGE_MED"] = medium_threshold_branch
    data["BRANCH_COVERAGE_HIGH"] = high_threshold_branch

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

    root_info.set_coverage(covdata)

    # Generate the coverage output (on a per-package basis)
    # source_dirs = set()
    files = []
    dirs = []
    filtered_fname = ""
    keys = sort_coverage(
        covdata,
        show_branch=False,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent,
    )
    cdata_fname = {}
    cdata_sourcefile = {}
    for f in keys:
        filtered_fname = options.root_filter.sub("", f)
        files.append(filtered_fname)
        dirs.append(os.path.dirname(filtered_fname) + os.sep)
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

    for f in keys:
        root_info.add_file(covdata[f], cdata_sourcefile[f], cdata_fname[f])

    if options.html_details:
        (output_prefix, output_suffix) = os.path.splitext(os.path.abspath(output_file))
        if output_suffix == "":
            output_suffix = ".html"
        functions_fname = f"{output_prefix}.functions{output_suffix}"
        data["FUNCTIONS_FNAME"] = os.path.basename(functions_fname)
    html_string = templates().get_template("root_page.html").render(**data)
    with open_text_for_writing(
        output_file, encoding=options.html_encoding, errors="xmlcharrefreplace"
    ) as fh:
        fh.write(html_string + "\n")

    # Return, if no details are requested
    if not options.html_details:
        return

    #
    # Generate an HTML file for every source file
    #
    error_occurred = False
    all_functions = dict()
    for f in keys:
        cdata = covdata[f]

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

        def coverage_class(percent: Optional[float]) -> str:
            return coverage_to_class(percent, medium_threshold, high_threshold)

        def line_coverage_class(percent: Optional[float]) -> str:
            return coverage_to_class(
                percent, medium_threshold_line, high_threshold_line
            )

        def branch_coverage_class(percent: Optional[float]) -> str:
            return coverage_to_class(
                percent, medium_threshold_branch, high_threshold_branch
            )

        data["lines"] = dict_from_stat(cdata.line_coverage(), line_coverage_class)
        data["functions"] = dict_from_stat(cdata.function_coverage(), coverage_class)
        data["branches"] = dict_from_stat(
            cdata.branch_coverage(), branch_coverage_class
        )
        data["decisions"] = dict_from_stat(cdata.decision_coverage(), coverage_class)

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


def dict_from_stat(
    stat: Union[CoverageStat, DecisionCoverageStat],
    coverage_class: Callable[[Optional[float]], str],
    default: float = None,
) -> dict:
    coverage_default = "-" if default is None else default
    data = {
        "total": stat.total,
        "exec": stat.covered,
        "coverage": stat.percent_or(coverage_default),
        "class": coverage_class(stat.percent_or(default)),
    }

    if isinstance(stat, DecisionCoverageStat):
        data["unchecked"] = stat.uncheckable

    return data


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


def source_row_decision(decision: DecisionCoverage) -> Optional[dict]:
    if decision is None:
        return None

    items = []

    if isinstance(decision, DecisionCoverageUncheckable):
        items.append(
            {
                "uncheckable": True,
            }
        )
    elif isinstance(decision, DecisionCoverageConditional):
        items.append(
            {
                "uncheckable": False,
                "taken": decision.count_true > 0,
                "count": decision.count_true,
                "name": "true",
            }
        )
        items.append(
            {
                "uncheckable": False,
                "taken": decision.count_false > 0,
                "count": decision.count_false,
                "name": "false",
            }
        )
    elif isinstance(decision, DecisionCoverageSwitch):
        items.append(
            {
                "uncheckable": False,
                "taken": decision.count > 0,
                "count": decision.count,
                "name": "true",
            }
        )
    else:
        raise RuntimeError(f"Unknown decision type {decision!r}")

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
