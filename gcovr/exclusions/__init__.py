# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.2
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2024 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""
Handle exclusion markers and any other source code level filtering mechanisms.

The different mechanisms are exposed as separate passes/functions
that remove unwanted aspects from the coverage data.
Alternatively, they full suite of exclusion rules can be invoked
via ``apply_all_exclusions()``, which is configured via the usual options object.
"""

from dataclasses import dataclass, field
import re
from typing import List, Optional
import logging

from .utils import (
    _make_is_in_any_range_inclusive,
    apply_exclusion_ranges,
    function_exclude_not_supported,
    get_function_exclude_ranges,
    get_functions_by_line,
)

from ..coverage import FileCoverage
from .markers import ExclusionPredicate, FunctionListByLine, apply_exclusion_markers
from .noncode import remove_unreachable_branches, remove_noncode_lines

LOGGER = logging.getLogger("gcovr")


@dataclass
class ExclusionOptions:
    """
    Options used by exclusion processing.

    The defaults are just for testing purposes.
    Otherwise, this class acts more like an interface,
    describing some options in "gcovr.configuration".
    """

    respect_exclusion_markers: bool = True
    exclude_functions: List[re.Pattern] = field(default_factory=lambda: [])
    exclude_lines_by_pattern: Optional[str] = None
    exclude_branches_by_pattern: Optional[str] = None
    exclude_pattern_prefix: str = "PREFIX"
    exclude_throw_branches: bool = False
    exclude_unreachable_branches: bool = False
    exclude_function_lines: bool = False
    exclude_internal_functions: bool = False
    exclude_noncode_lines: bool = False
    exclude_calls: bool = True


def apply_all_exclusions(
    filecov: FileCoverage,
    *,
    lines: List[str],
    options: ExclusionOptions,
) -> None:
    """
    Apply all available exclusion mechanisms, if they are enabled by the options.

    Modifies the FileCoverage in place.
    """

    if options.exclude_noncode_lines:
        remove_noncode_lines(filecov, lines=lines)

    if options.respect_exclusion_markers:
        apply_exclusion_markers(
            filecov,
            lines=lines,
            exclude_lines_by_pattern=options.exclude_lines_by_pattern,
            exclude_branches_by_pattern=options.exclude_branches_by_pattern,
            exclude_pattern_prefix=options.exclude_pattern_prefix,
        )

    if options.exclude_functions:
        remove_functions(filecov, options.exclude_functions)

    if options.exclude_throw_branches:
        remove_throw_branches(filecov)

    if options.exclude_unreachable_branches:
        remove_unreachable_branches(filecov, lines=lines)

    if options.exclude_function_lines:
        remove_function_lines(filecov)

    if options.exclude_internal_functions:
        remove_internal_functions(filecov)

    if options.exclude_calls:
        remove_calls(filecov)


def remove_calls(filecov: FileCoverage):
    """Remove the information about calls."""

    # Clear the calls of each line.
    for line in filecov.lines.values():
        line.calls.clear()


def remove_internal_functions(filecov: FileCoverage):
    """Remove compiler-generated functions, e.g. for static initialization."""

    # Get all the keys first because we want to remove some of them which will else result in an error.
    for key in list(filecov.functions.keys()):
        function = filecov.functions[key]
        if _function_can_be_excluded(function.demangled_name):
            LOGGER.debug(
                "Ignoring symbol %s in line %s in file %s",
                function.demangled_name,
                ", ".join([str(line) for line in sorted(function.count.keys())]),
                filecov.filename,
            )

            # Remove function and exclude the related lines
            filecov.functions.pop(key)
            for linecov in filecov.lines.values():
                if (
                    linecov.function_name is not None
                    and linecov.function_name == function.name
                ):
                    linecov.excluded = True
                    linecov.branches = {}
                    linecov.count = 0


def _function_can_be_excluded(name: str) -> bool:
    """special names for construction/destruction of static objects will be ignored"""
    return name.startswith("__") or name.startswith("_GLOBAL__sub_I_")


def remove_function_lines(filecov: FileCoverage) -> None:
    """Remove coverage for lines that contain a function definition."""
    # iterate over a shallow copy
    known_function_lines = set(
        line
        for function in filecov.functions.values()
        for line in function.count.keys()
    )
    for linecov in list(filecov.lines.values()):
        if linecov.lineno in known_function_lines:
            filecov.lines.pop(linecov.lineno)


def remove_throw_branches(filecov: FileCoverage) -> None:
    """Remove branches annotated as "throw"."""
    for linecov in filecov.lines.values():
        # iterate over shallow copy
        for branch_id, branch in list(linecov.branches.items()):
            if branch.throw:
                LOGGER.debug(
                    "Excluding unreachable branch on line %d file %s: detected as exception-only code",
                    linecov.lineno,
                    filecov.filename,
                )
                linecov.branches.pop(branch_id)


def remove_functions(filecov: FileCoverage, patterns: List[re.Pattern]) -> None:
    """Remove matching functions"""
    if filecov.functions:
        if filecov.functions[list(filecov.functions.keys())[0]].start is None:
            function_exclude_not_supported()
        else:
            functions_by_line: FunctionListByLine = get_functions_by_line(filecov)

            exclude_ranges = []
            for lineno, functions in functions_by_line.items():
                for function in functions:
                    for pattern in patterns:
                        if pattern.fullmatch(function.demangled_name):
                            exclude_ranges += get_function_exclude_ranges(
                                filecov.filename,
                                lineno,
                                function.start[lineno][1]
                                + 1,  # Cheat that the comment is after the definition
                                functions_by_line=functions_by_line,
                            )
                            break
            LOGGER.debug(
                f"Exclusion range for functions from CLI in {filecov.filename}: {str(exclude_ranges)}."
            )
            exclusion_predicate: ExclusionPredicate = _make_is_in_any_range_inclusive(
                exclude_ranges
            )
            apply_exclusion_ranges(
                filecov,
                line_is_excluded=exclusion_predicate,
                branch_is_excluded=exclusion_predicate,
            )
