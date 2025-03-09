# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from typing import Any, Optional

from ...data_model.container import CoverageContainer
from ...data_model.stats import SummarizedStats
from ...options import Options
from ...utils import (
    presentable_filename,
    open_text_for_writing,
)
from jinja2 import (
    BaseLoader,
    Environment,
    ChoiceLoader,
    FileSystemLoader,
    FunctionLoader,
    PackageLoader,
    Template,
)


# markdown_theme string is <theme_directory>.<color> or only <color> (if only color use default)
# examples: github.green github.blue or blue or green
def get_theme_name(theme: str) -> str:
    """Get the theme name without the color."""
    return theme.split(".")[0] if "." in theme else "default"


def templates(options: Options) -> Environment:
    loader: BaseLoader = PackageLoader(
        "gcovr.formats.markdown",
        package_path=get_theme_name(options.markdown_theme),
    )

    return Environment(
        loader=loader,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce the gcovr report in markdown"""

    data = {"info": {"summary": options.markdown_summary is not None}}

    with open_text_for_writing(output_file, "coverage.md") as fh:
        summary = _summary_from_stats(covdata.stats, options)
        data["info"].update(summary)

        # Data
        sorted_keys = covdata.sort_coverage(
            sort_key=options.sort_key,
            sort_reverse=options.sort_reverse,
            by_metric="branch" if options.sort_branches else "line",
        )

        data["entries"] = list()
        for key in sorted_keys:
            summary = _summary_from_stats(covdata[key].stats, options)
            summary["filename"] = presentable_filename(
                covdata[key].filename, options.root_filter
            )
            data["entries"].append(summary)

        markdown_string = (
            templates(options).get_template("report_template.md").render(**data)
        )
        fh.write(markdown_string)


def _coverage_to_badge(
    coverage: Optional[float],
    medium_threshold: float,
    high_threshold: float,
    theme: str,
) -> str:
    if coverage is None:
        return "⚫"
    elif coverage >= high_threshold:
        return "🔵" if theme == "blue" else "🟢"
    elif coverage >= medium_threshold:
        return "🟡"
    else:
        return "🔴"


def _summary_from_stats(stats: SummarizedStats, options: Options) -> dict[str, Any]:
    summary = dict[str, Any]()

    summary["line_badge"] = _coverage_to_badge(
        stats.line.percent,
        options.medium_threshold_line,
        options.high_threshold_line,
        options.markdown_theme,
    )
    summary["function_badge"] = _coverage_to_badge(
        stats.function.percent,
        options.medium_threshold,
        options.high_threshold,
        options.markdown_theme,
    )
    summary["branch_badge"] = _coverage_to_badge(
        stats.branch.percent,
        options.medium_threshold_branch,
        options.high_threshold_branch,
        options.markdown_theme,
    )
    summary["line_covered"] = stats.line.covered
    summary["line_total"] = stats.line.total
    summary["line_percent"] = stats.line.percent_or(0.0)
    summary["function_covered"] = stats.function.covered
    summary["function_total"] = stats.function.total
    summary["function_percent"] = stats.function.percent_or(0.0)
    summary["branch_covered"] = stats.branch.covered
    summary["branch_total"] = stats.branch.total
    summary["branch_percent"] = stats.branch.percent_or(0.0)

    return summary
