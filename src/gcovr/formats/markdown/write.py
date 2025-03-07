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

SUMMARY_TEMPLATE = """# Test coverage
## 📂 Overall coverage
|               | Coverage                                                                   |
|---------------|----------------------------------------------------------------------------|
| **Lines**     | {line_badge} {line_covered}/{line_total} ({line_percent}%)                 |
| **Functions** | {function_badge} {function_covered}/{function_total} ({function_percent}%) |
| **Branches**  | {branch_badge} {branch_covered}/{branch_total} ({branch_percent}%)         |
"""

FILE_HEADER = """## 📄 File coverage
| File | Lines | Functions | Branches |
|------|-------|-----------|----------|
"""

FILE_TEMPLATE = (
    "| **`{filename}`**"
    " | {line_badge} {line_covered}/{line_total} ({line_percent}%)"
    " | {function_badge} {function_covered}/{function_total} ({function_percent}%)"
    " | {branch_badge} {branch_covered}/{branch_total} ({branch_percent}%) |\n"
)


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce the gcovr report in markdown"""

    with open_text_for_writing(output_file, "coverage.md") as fh:
        summary = _summary_from_stats(covdata.stats, options)
        fh.write(SUMMARY_TEMPLATE.format(**summary))
        fh.write(FILE_HEADER)

        # Data
        sorted_keys = covdata.sort_coverage(
            sort_key=options.sort_key,
            sort_reverse=options.sort_reverse,
            by_metric="branch" if options.sort_branches else "line",
        )

        for key in sorted_keys:
            summary = _summary_from_stats(covdata[key].stats, options)
            summary["filename"] = presentable_filename(
                covdata[key].filename, options.root_filter
            )
            fh.write(FILE_TEMPLATE.format(**summary))


def write_summary_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce the gcovr summary report in markdown"""

    with open_text_for_writing(output_file, "coverage.md") as fh:
        summary = _summary_from_stats(covdata.stats, options)
        fh.write(SUMMARY_TEMPLATE.format(**summary))


def _coverage_to_badge(
    coverage: Optional[float], medium_threshold: float, high_threshold: float
) -> str:
    if coverage is None:
        return "⚫"
    elif coverage >= high_threshold:
        return "🟢"
    elif coverage >= medium_threshold:
        return "🟡"
    else:
        return "🔴"


def _summary_from_stats(stats: SummarizedStats, options: Options) -> dict[str, Any]:
    summary = dict[str, Any]()

    summary["line_badge"] = _coverage_to_badge(
        stats.line.percent, options.md_medium_threshold, options.md_high_threshold
    )
    summary["function_badge"] = _coverage_to_badge(
        stats.function.percent, options.md_medium_threshold, options.md_high_threshold
    )
    summary["branch_badge"] = _coverage_to_badge(
        stats.branch.percent, options.md_medium_threshold, options.md_high_threshold
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
