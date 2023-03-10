# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
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
from typing import Any, Callable, Dict, Optional, Union

from ...version import __version__
from ...utils import (
    force_unix_separator,
    realpath,
    commonpath,
    open_text_for_writing,
)
from ...coverage import (
    CallCoverage,
    CovData,
    CoverageStat,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageStat,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    DirectoryCoverage,
    FileCoverage,
    LineCoverage,
    SummarizedStats,
    sort_coverage,
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
        loader=PackageLoader("gcovr.writer.html"),
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

    THEMES = ["green", "blue"]

    @staticmethod
    def get_themes():
        return CssRenderer.THEMES

    @staticmethod
    def get_default_theme():
        return CssRenderer.THEMES[0]

    @staticmethod
    def load_css_template(options):
        if options.html_css is not None:
            template_path = os.path.relpath(options.html_css)
            return user_templates().get_template(template_path)

        return templates().get_template("style.css")

    @staticmethod
    def render(options):
        template = CssRenderer.load_css_template(options)
        return template.render(
            tab_size=options.html_tab_size,
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
        if options.html_syntax_highlighting
        else NullHighlighting()
    )


def coverage_to_class(coverage, medium_threshold, high_threshold) -> str:
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
    def __init__(self, options) -> None:
        self.medium_threshold = options.html_medium_threshold
        self.high_threshold = options.html_high_threshold
        self.medium_threshold_line = options.html_medium_threshold_line
        self.high_threshold_line = options.html_high_threshold_line
        self.medium_threshold_branch = options.html_medium_threshold_branch
        self.high_threshold_branch = options.html_high_threshold_branch
        self.link_function_list = options.html_details or options.html_nested
        self.relative_anchors = options.relative_anchors

        self.version = __version__
        self.head = options.html_title
        self.date = options.timestamp.isoformat(sep=" ", timespec="seconds")
        self.encoding = options.html_encoding
        self.directory = None
        self.branches = dict()
        self.decisions = dict()
        self.calls = dict()
        self.functions = dict()
        self.lines = dict()
        self.files = []
        self.subdirs = dict()

    def set_directory(self, directory) -> None:
        self.directory = directory

    def get_directory(self) -> str:
        return "." if self.directory == "" else force_unix_separator(self.directory)

    def set_coverage(self, covdata: CovData) -> None:
        """Update this RootInfo with a summary of the CovData."""
        stats = SummarizedStats.from_covdata(covdata)
        self.lines = dict_from_stat(stats.line, self._line_coverage_to_class, 0.0)
        self.functions = dict_from_stat(stats.function, self._coverage_to_class)
        self.branches = dict_from_stat(stats.branch, self._branch_coverage_to_class)
        self.decisions = dict_from_stat(stats.decision, self._coverage_to_class)
        self.calls = dict_from_stat(stats.call, self._coverage_to_class)

    def clear_files(self) -> None:
        self.files = []

    def add_file(
        self, cdata: Union[DirectoryCoverage, FileCoverage], link_report, cdata_fname
    ) -> None:
        stats = (
            cdata.stats
            if isinstance(cdata, DirectoryCoverage)
            else SummarizedStats.from_file(cdata)
        )

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

        calls = {
            "total": stats.call.total,
            "exec": stats.call.covered,
            "coverage": stats.call.percent_or("-"),
            "class": self._coverage_to_class(stats.call.percent),
        }

        display_filename = force_unix_separator(
            os.path.relpath(realpath(cdata_fname), self.directory)
        )

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
                calls=calls,
                functions=functions,
            )
        )

    def _coverage_to_class(self, coverage) -> str:
        return coverage_to_class(coverage, self.medium_threshold, self.high_threshold)

    def _line_coverage_to_class(self, coverage) -> str:
        return coverage_to_class(
            coverage, self.medium_threshold_line, self.high_threshold_line
        )

    def _branch_coverage_to_class(self, coverage) -> str:
        return coverage_to_class(
            coverage, self.medium_threshold_branch, self.high_threshold_branch
        )


#
# Produce an HTML report
#
def print_html_report(covdata: CovData, output_file: str, options) -> bool:
    css_data = CssRenderer.render(options)
    medium_threshold = options.html_medium_threshold
    high_threshold = options.html_high_threshold
    medium_threshold_line = options.html_medium_threshold_line
    high_threshold_line = options.html_high_threshold_line
    medium_threshold_branch = options.html_medium_threshold_branch
    high_threshold_branch = options.html_high_threshold_branch
    exclude_calls = options.exclude_calls
    show_decision = options.show_decision

    data = {}
    root_info = RootInfo(options)
    data["info"] = root_info

    data["SHOW_DECISION"] = show_decision
    data["EXCLUDE_CALLS"] = exclude_calls
    data["COVERAGE_MED"] = medium_threshold
    data["COVERAGE_HIGH"] = high_threshold
    data["LINE_COVERAGE_MED"] = medium_threshold_line
    data["LINE_COVERAGE_HIGH"] = high_threshold_line
    data["BRANCH_COVERAGE_MED"] = medium_threshold_branch
    data["BRANCH_COVERAGE_HIGH"] = high_threshold_branch

    self_contained = options.html_self_contained
    if self_contained is None:
        self_contained = not (options.html_details or options.html_nested)
    if output_file == "-":
        if not self_contained:
            raise ArgumentTypeError(
                "Only self contained reports can be printed to STDOUT"
            )
        elif options.html_details or options.html_nested:
            raise ArgumentTypeError("Detailed reports can not be printed to STDOUT")

    if output_file.endswith(os.sep):
        if options.html_nested:
            output_file += "coverage_nested.html"
        elif options.html_details:
            output_file += "coverage_details.html"
        else:
            output_file += "coverage.html"

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

    data["theme"] = options.html_theme

    root_info.set_coverage(covdata)

    # Generate the coverage output (on a per-package basis)
    # source_dirs = set()
    files = []
    filtered_fname = ""
    sorted_keys = sort_coverage(
        covdata,
        show_branch=False,
        filename_uses_relative_pathname=True,
        by_num_uncovered=options.sort_uncovered,
        by_percent_uncovered=options.sort_percent,
    )

    if options.html_nested:
        root_info.subdirs = DirectoryCoverage.from_covdata(
            covdata, sorted_keys, options.root_filter
        )
        DirectoryCoverage.collapse_subdirectories(
            root_info.subdirs, options.root_filter
        )

    cdata_fname = {}
    cdata_sourcefile = {}
    for f in sorted_keys + list(root_info.subdirs.keys()):
        filtered_fname = options.root_filter.sub("", f)
        files.append(filtered_fname)
        cdata_fname[f] = filtered_fname
        if options.html_details or options.html_nested:
            if os.path.normpath(f) == os.path.normpath(options.root_dir):
                cdata_sourcefile[f] = output_file
            else:
                cdata_sourcefile[f] = _make_short_sourcename(
                    output_file, filtered_fname
                )
        else:
            cdata_sourcefile[f] = None

    # Define the common root directory, which may differ from options.root_dir
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

    if options.html_details or options.html_nested:
        (output_prefix, output_suffix) = os.path.splitext(os.path.abspath(output_file))
        if output_suffix == "":
            output_suffix = ".html"
        functions_output_file = f"{output_prefix}.functions{output_suffix}"
        data["FUNCTIONS_FNAME"] = os.path.basename(functions_output_file)

    if options.html_nested:
        write_directory_pages(
            output_file,
            cdata_fname,
            cdata_sourcefile,
            options,
            root_info,
            data,
        )
    else:
        for f in sorted_keys:
            root_info.add_file(covdata[f], cdata_sourcefile[f], cdata_fname[f])
        write_root_page(output_file, options, data)
        if not options.html_details:
            return False

    return write_source_pages(
        functions_output_file,
        covdata,
        cdata_fname,
        cdata_sourcefile,
        options,
        root_info,
        data,
    )


def write_root_page(output_file: str, options, data: Dict[str, Any]) -> None:
    #
    # Generate the root HTML file that contains the high level report
    #
    html_string = templates().get_template("directory_page.html").render(**data)
    with open_text_for_writing(
        output_file, encoding=options.html_encoding, errors="xmlcharrefreplace"
    ) as fh:
        fh.write(html_string + "\n")


def write_source_pages(
    functions_output_file: str,
    covdata: CovData,
    cdata_fname: Dict[str, str],
    cdata_sourcefile: Dict[str, str],
    options,
    root_info: RootInfo,
    data: Dict[str, Any],
) -> bool:
    #
    # Generate an HTML file for every source file
    #
    medium_threshold = options.html_medium_threshold
    high_threshold = options.html_high_threshold
    medium_threshold_line = options.html_medium_threshold_line
    high_threshold_line = options.html_high_threshold_line
    medium_threshold_branch = options.html_medium_threshold_branch
    high_threshold_branch = options.html_high_threshold_branch
    formatter = get_formatter(options)
    error_occurred = False

    all_functions = dict()
    for f, cdata in covdata.items():
        data["filename"] = cdata_fname[f]
        root_info.add_file(cdata, cdata_sourcefile[f], cdata_fname[f])

        # Only use demangled names (containing a brace)
        data["function_list"] = []
        for name in sorted(cdata.functions.keys()):
            fcdata = cdata.functions[name]
            for lineno in sorted(fcdata.count.keys()):
                fdata = dict()
                fdata["name"] = name
                fdata["filename"] = cdata_fname[f]
                fdata["html_filename"] = os.path.basename(cdata_sourcefile[f])
                fdata["line"] = lineno
                fdata["count"] = fcdata.count[lineno]
                fdata["excluded"] = fcdata.excluded[lineno]

                data["function_list"].append(fdata)
                all_functions[(fdata["name"], fdata["filename"], fdata["line"])] = fdata

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
        data["calls"] = dict_from_stat(cdata.call_coverage(), coverage_class)

        parent_directory_key = cdata.parent_key
        if parent_directory_key:
            data["parent_link"] = os.path.basename(
                cdata_sourcefile[parent_directory_key]
            )
            data["parent_directory"] = cdata_fname[parent_directory_key]

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
                ctr = 0
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
            # Python ranges are exclusive. We want to iterate over all lines, including
            # that last line. Thus, we have to add a +1 to include that line.
            for ctr in range(1, max_line_from_cdata + 1):
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
        functions_output_file,
        encoding=options.html_encoding,
        errors="xmlcharrefreplace",
    ) as fh:
        fh.write(html_string + "\n")

    return error_occurred


def write_directory_pages(
    output_file: str,
    cdata_fname: Dict[str, str],
    cdata_sourcefile: Dict[str, str],
    options,
    root_info: RootInfo,
    data: Dict[str, Any],
) -> None:
    root_key = DirectoryCoverage.directory_root(root_info.subdirs, options.root_filter)

    for f, directory in root_info.subdirs.items():
        data["directory"] = commonpath(cdata_fname[f])

        data["date"] = root_info.date

        parent_directory_key = directory.parent_key
        if parent_directory_key:
            data["parent_link"] = os.path.basename(
                cdata_sourcefile[parent_directory_key]
            )
            data["parent_directory"] = cdata_fname[parent_directory_key]
        else:
            data["parent_link"] = None
            data["parent_directory"] = None

        sorted_files = sort_coverage(
            directory.children,
            show_branch=False,
            filename_uses_relative_pathname=True,
            by_num_uncovered=options.sort_uncovered,
            by_percent_uncovered=options.sort_percent,
        )

        root_info.clear_files()
        for key in sorted_files:
            fname = directory.children[key].filename

            root_info.add_file(
                directory.children[key], cdata_sourcefile[fname], cdata_fname[fname]
            )

        html_string = templates().get_template("directory_page.html").render(**data)
        filename = None
        if f == root_key:
            filename = output_file
        elif f in cdata_sourcefile:
            filename = cdata_sourcefile[f]
        else:
            logger.warning(
                f"There's a subdirectory {f} that there's no source files within it"
            )

        if filename:
            with open_text_for_writing(
                filename, encoding=options.html_encoding, errors="xmlcharrefreplace"
            ) as fh:
                fh.write(html_string + "\n")


def dict_from_stat(
    stat: Union[CoverageStat, DecisionCoverageStat],
    coverage_class: Callable[[Optional[float]], str],
    default: float = None,
) -> Dict[str, Any]:
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


def source_row(
    lineno: int, source: str, line_cov: Optional[LineCoverage]
) -> Dict[str, Any]:
    linebranch = None
    linedecision = None
    linecall = None
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
        linecall = source_row_call(line_cov.calls)
    return {
        "lineno": lineno,
        "source": source,
        "covclass": covclass,
        "linebranch": linebranch,
        "linedecision": linedecision,
        "linecall": linecall,
        "linecount": linecount,
    }


def source_row_branch(branches) -> Dict[str, Any]:
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


def source_row_call(calls: Optional[CallCoverage]) -> Dict[str, Any]:
    if not calls:
        return None

    invoked = 0
    total = 0
    items = []

    for call_id in sorted(calls):
        call = calls[call_id]
        if call.is_covered:
            invoked += 1
        total += 1
        items.append(
            {
                "invoked": call.is_covered,
                "name": call_id,
            }
        )

    return {
        "invoked": invoked,
        "total": total,
        "calls": items,
    }


def source_row_decision(
    decision: Optional[DecisionCoverage],
) -> Optional[Dict[str, Any]]:
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


def _make_short_sourcename(output_file: str, filename: str) -> str:
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
