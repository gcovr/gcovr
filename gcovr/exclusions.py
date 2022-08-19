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

"""
Handle exclusion markers and any other source code level filtering mechanisms.

The different mechanisms are exposed as separate passes/functions
that remove unwanted aspects from the coverage data.
Alternatively, they full suite of exclusion rules can be invoked
via ``apply_all_exclusions()``, which is configured via the usual options object.
"""

from dataclasses import dataclass
from typing import List, Optional, Callable, Tuple, Iterable
import logging
import re

from .coverage import FileCoverage


logger = logging.getLogger("gcovr")

_EXCLUDE_FLAG = "_EXCL_"
_EXCLUDE_LINE_WORD = ""
_EXCLUDE_BRANCH_WORD = "BR_"
_EXCLUDE_PATTERN_POSTFIX = "(LINE|START|STOP)"

_C_STYLE_COMMENT_PATTERN = re.compile(r"/\*.*?\*/")
_CPP_STYLE_COMMENT_PATTERN = re.compile(r"//.*?$")

ExclusionPredicate = Callable[[int], bool]


@dataclass
class ExclusionOptions:
    """
    Options used by exclusion processing.

    The defaults are just for testing purposes.
    Otherwise, this class acts more like an interface,
    describing some options in "gcovr.configuration".
    """

    respect_exclusion_markers: bool = True
    exclude_lines_by_pattern: Optional[str] = None
    exclude_branches_by_pattern: Optional[str] = None
    exclude_pattern_prefix: str = "PREFIX"
    exclude_throw_branches: bool = False
    exclude_unreachable_branches: bool = False
    exclude_function_lines: bool = False
    exclude_internal_functions: bool = False


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

    remove_noncode_lines(filecov, lines=lines)

    if options.respect_exclusion_markers:
        apply_exclusion_markers(
            filecov,
            lines=lines,
            exclude_lines_by_pattern=options.exclude_lines_by_pattern,
            exclude_branches_by_pattern=options.exclude_branches_by_pattern,
            exclude_pattern_prefix=options.exclude_pattern_prefix,
        )

    if options.exclude_throw_branches:
        remove_throw_branches(filecov)

    if options.exclude_unreachable_branches:
        remove_unreachable_branches(filecov, lines=lines)

    if options.exclude_function_lines:
        remove_function_lines(filecov)

    if options.exclude_internal_functions:
        remove_internal_functions(filecov)


def apply_exclusion_markers(
    filecov: FileCoverage,
    *,
    lines: List[str],
    exclude_lines_by_pattern: Optional[str],
    exclude_branches_by_pattern: Optional[str],
    exclude_pattern_prefix: str,
) -> None:
    """
    Remove any coverage information that is excluded by explicit markers such as
    ``GCOVR_EXCL_LINE``.

    Modifies the input FileCoverage in place.

    Arguments:
        filecov: the coverage to filter
        lines: the source code lines (not raw gcov lines)
        exclude_lines_by_pattern: string with regex syntax to exclude
            individual lines
        exclude_branches_by_pattern: string with regex syntax to exclude
            individual branches
        exclude_pattern_prefix: string with prefix for _LINE/_START/_STOP markers.
    """

    line_is_excluded, branch_is_excluded = _find_excluded_ranges(
        lines=lines,
        warnings=_ExclusionRangeWarnings(filecov.filename),
        exclude_lines_by_custom_pattern=exclude_lines_by_pattern,
        exclude_branches_by_custom_pattern=exclude_branches_by_pattern,
        exclude_pattern_prefix=exclude_pattern_prefix,
    )

    for linecov in filecov.lines.values():
        # always erase decision coverage since exclusions can change analysis
        linecov.decision = None

        if line_is_excluded(linecov.lineno):
            linecov.excluded = True
            linecov.branches = {}
            linecov.count = 0

        elif branch_is_excluded(linecov.lineno):
            linecov.branches = {}


def remove_internal_functions(filecov: FileCoverage):
    """Remove compiler-generated functions, e.g. for static initialization."""

    # iterate over shallow copy
    for function in list(filecov.functions.values()):
        if _function_can_be_excluded(function.name):
            logger.debug(
                "Ignoring symbol %s in line %d in file %s",
                function.name,
                function.lineno,
                filecov.filename,
            )

            filecov.functions.pop(function.name)


def _function_can_be_excluded(name: str) -> bool:
    """special names for construction/destruction of static objects will be ignored"""
    return name.startswith("__") or name.startswith("_GLOBAL__sub_I_")


def remove_function_lines(filecov: FileCoverage) -> None:
    """Remove coverage for lines that contain a function definition."""
    # iterate over a shallow copy
    known_function_lines = set(
        function.lineno for function in filecov.functions.values()
    )
    for linecov in list(filecov.lines.values()):
        if linecov.lineno in known_function_lines:
            filecov.lines.pop(linecov.lineno)


def remove_throw_branches(filecov: FileCoverage) -> None:
    """Remove branches annotated as "throw"."""
    for linecov in filecov.lines.values():
        # iterate over shallow copy
        for branch_id, branch in list(linecov.branches.items()):
            if not branch.throw:
                continue

            logger.debug(
                "Excluding unreachable branch on line %d file %s: detected as exception-only code",
                linecov.lineno,
                filecov.filename,
            )
            linecov.branches.pop(branch_id)


def remove_unreachable_branches(filecov: FileCoverage, *, lines: List[str]) -> None:
    """Remove branches on lines that look like they don't contain useful code."""
    for linecov in filecov.lines.values():
        if not linecov.branches:
            continue

        if _line_can_contain_branches(lines[linecov.lineno - 1]):
            continue

        logger.debug(
            "Excluding unreachable branch on line %d file %s: detected as compiler-generated code",
            linecov.lineno,
            filecov.filename,
        )

        linecov.branches = {}


def remove_noncode_lines(filecov: FileCoverage, *, lines: List[str]) -> None:
    """Remove lines that look like non-code."""
    # iterate over a shallow copy
    for linecov in list(filecov.lines.values()):
        source_code = lines[linecov.lineno - 1]
        if linecov.count == 0 and _is_non_code(source_code):
            filecov.lines.pop(linecov.lineno)


def _line_can_contain_branches(code: str) -> bool:
    """
    False if the line looks empty except for braces.

    >>> _line_can_contain_branches('} // end something')
    False
    >>> _line_can_contain_branches('foo();')
    True
    """

    code = _CPP_STYLE_COMMENT_PATTERN.sub("", code)
    code = _C_STYLE_COMMENT_PATTERN.sub("", code)
    code = code.strip().replace(" ", "")
    return code not in ["", "{", "}", "{}"]


def _is_non_code(code: str) -> bool:
    """
    Check for patterns that indicate that this line doesn't contain useful code.

    Examples:
    >>> _is_non_code('  // some comment!')
    True
    >>> _is_non_code('  /* some comment! */')
    True
    >>> _is_non_code('} else {')  # could be easily made detectable
    False
    >>> _is_non_code('}else{')
    False
    >>> _is_non_code('else')
    True
    >>> _is_non_code('{')
    True
    >>> _is_non_code('/* some comment */ {')
    True
    >>> _is_non_code('}')
    True
    >>> _is_non_code('} // some code')
    True
    >>> _is_non_code('return {};')
    False
    """

    code = _CPP_STYLE_COMMENT_PATTERN.sub("", code)
    code = _C_STYLE_COMMENT_PATTERN.sub("", code)
    code = code.strip()
    return len(code) == 0 or code in ["{", "}", "else"]


class _ExclusionRangeWarnings:
    r"""
    Log warnings related to exclusion marker processing.

    Example:
    >>> source = '''\
    ... some code
    ... foo // LCOV_EXCL_STOP
    ... bar // GCOVR_EXCL_START
    ... bar // GCOVR_EXCL_LINE
    ... baz // GCOV_EXCL_STOP
    ... "GCOVR_EXCL_START"
    ... '''
    >>> caplog = getfixture('caplog')
    >>> caplog.clear()
    >>> _ = apply_exclusion_markers(  # doctest: +NORMALIZE_WHITESPACE
    ...     FileCoverage('example.cpp'),
    ...     lines=source.strip().splitlines(),
    ...     exclude_lines_by_pattern=None,
    ...     exclude_branches_by_pattern=None,
    ...     exclude_pattern_prefix='[GL]COVR?')
    >>> for message in caplog.record_tuples:
    ...     print(f"{message[1]}: {message[2]}")
    30: mismatched coverage exclusion flags.
              LCOV_EXCL_STOP found on line 2 without corresponding LCOV_EXCL_START, when processing example.cpp.
    30: GCOVR_EXCL_LINE found on line 4 in excluded region started on line 3, when processing example.cpp.
    30: GCOVR_EXCL_START found on line 3 was terminated by GCOV_EXCL_STOP on line 5, when processing example.cpp.
    30: The coverage exclusion region start flag GCOVR_EXCL_START
              on line 6 did not have corresponding GCOVR_EXCL_STOP flag
              in file example.cpp.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def mismatched_start_stop(
        self, start_lineno: int, start: str, stop_lineno: int, stop: str
    ) -> None:
        """warn that start/stop region markers don't match"""
        logger.warning(
            f"{start} found on line {start_lineno} "
            f"was terminated by {stop} on line {stop_lineno}, "
            f"when processing {self.filename}."
        )

    def stop_without_start(self, lineno: int, expected_start: str, stop: str) -> None:
        """warn that a region was ended without corresponding start marker"""
        logger.warning(
            "mismatched coverage exclusion flags.\n"
            f"          {stop} found on line {lineno} without corresponding {expected_start}, "
            f"when processing {self.filename}."
        )

    def start_without_stop(self, lineno: int, start: str, expected_stop: str) -> None:
        """warn that a region was started but not closed"""
        logger.warning(
            f"The coverage exclusion region start flag {start}\n"
            f"          on line {lineno} did not have corresponding {expected_stop} flag\n"
            f"          in file {self.filename}."
        )

    def line_after_start(self, lineno: int, start: str, start_lineno: int) -> None:
        """warn that a region was started but an excluded line was found"""
        logger.warning(
            f"{start} found on line {lineno} in excluded region started on line {start_lineno}, "
            f"when processing {self.filename}."
        )


def _process_exclusion_marker(
    lineno: int,
    flag: str,
    header: str,
    exclude_word: str,
    warnings: _ExclusionRangeWarnings,
    exclude_ranges: List[Tuple[int, int]],
    exclusion_stack: List[Tuple[str, int]],
) -> None:
    """
    Process the exclusion marker.

    Header is a marker name like LCOV or GCOVR.

    START flags are added to the exlusion stack
    STOP flags remove a marker from the exclusion stack
    """

    if flag == "LINE":
        if exclusion_stack:
            warnings.line_after_start(
                lineno,
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "LINE",
                exclusion_stack[-1][1],
            )
        else:
            exclude_ranges.append((lineno, lineno))

    if flag == "START":
        exclusion_stack.append((header, lineno))

    elif flag == "STOP":
        if not exclusion_stack:
            warnings.stop_without_start(
                lineno,
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "START",
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "STOP",
            )
        else:
            start_header, start_lineno = exclusion_stack.pop()
            if header != start_header:
                warnings.mismatched_start_stop(
                    start_lineno,
                    f"{start_header}" + _EXCLUDE_FLAG + exclude_word + "START",
                    lineno,
                    f"{header}" + _EXCLUDE_FLAG + exclude_word + "STOP",
                )

            exclude_ranges.append((start_lineno, lineno))

    else:  # pragma: no cover
        pass


def _find_excluded_ranges(
    lines: List[str],
    *,
    warnings: _ExclusionRangeWarnings,
    exclude_lines_by_custom_pattern: Optional[str] = None,
    exclude_branches_by_custom_pattern: Optional[str] = None,
    exclude_pattern_prefix: str,
) -> Tuple[ExclusionPredicate, ExclusionPredicate]:
    """
    Scan through all lines to find line ranges and branch ranges covered by exclusion markers.

    Example:
    >>> lines = [
    ...     (11, '//PREFIX_EXCL_LINE'), (13, '//IGNORE_LINE'),
    ...     (15, '//PREFIX_EXCL_START'), (18, '//PREFIX_EXCL_STOP'),
    ...     (21, '//PREFIX_EXCL_BR_LINE'), (23, '//IGNORE_BR'),
    ...     (25, '//PREFIX_EXCL_BR_START'), (28, '//PREFIX_EXCL_BR_STOP')]
    >>> exclude_line, exclude_branch = _find_excluded_ranges(
    ...     _lines_from_sparse(lines), warnings=...,
    ...     exclude_lines_by_custom_pattern='.*IGNORE_LINE',
    ...     exclude_branches_by_custom_pattern='.*IGNORE_BR',
    ...     exclude_pattern_prefix='PREFIX')
    >>> [lineno for lineno in range(30) if exclude_line(lineno)]
    [11, 13, 15, 16, 17, 18]
    >>> [lineno for lineno in range(30) if exclude_branch(lineno)]
    [21, 23, 25, 26, 27, 28]

    The stop marker line is inclusive:
    >>> exclude_line, _ = _find_excluded_ranges(
    ...     _lines_from_sparse([(3, '// PREFIX_EXCL_START'), (6, '// PREFIX_EXCL_STOP')]),
    ...     warnings=...,
    ...     exclude_pattern_prefix='PREFIX')
    >>> for lineno in range(1, 10):
    ...     print(f"{lineno}: {'excluded' if exclude_line(lineno) else 'code'}")
    1: code
    2: code
    3: excluded
    4: excluded
    5: excluded
    6: excluded
    7: code
    8: code
    9: code
    """

    def find_range_impl(
        custom_pattern: Optional[str],
        exclude_word: str,
    ) -> ExclusionPredicate:
        custom_pattern_regex = None
        if custom_pattern:
            custom_pattern_regex = re.compile(custom_pattern)

        excl_pattern = re.compile(
            "("
            + exclude_pattern_prefix
            + ")"
            + _EXCLUDE_FLAG
            + exclude_word
            + _EXCLUDE_PATTERN_POSTFIX
        )

        # possibly overlapping inclusive (closed) ranges that describe exclusions regions
        exclude_ranges: List[Tuple[int, int]] = []
        exclusion_stack: List[Tuple[str, int]] = []

        for lineno, code in enumerate(lines, 1):
            if _EXCLUDE_FLAG in code:
                for header, flag in excl_pattern.findall(code):
                    _process_exclusion_marker(
                        lineno,
                        flag,
                        header,
                        exclude_word,
                        warnings,
                        exclude_ranges,
                        exclusion_stack,
                    )

            if custom_pattern_regex:
                if custom_pattern_regex.match(code):
                    exclude_ranges.append((lineno, lineno))

        for header, lineno in exclusion_stack:
            warnings.start_without_stop(
                lineno,
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "START",
                f"{header}" + _EXCLUDE_FLAG + exclude_word + "STOP",
            )

        return _make_is_in_any_range_inclusive(exclude_ranges)

    return (
        find_range_impl(exclude_lines_by_custom_pattern, _EXCLUDE_LINE_WORD),
        find_range_impl(exclude_branches_by_custom_pattern, _EXCLUDE_BRANCH_WORD),
    )


def _make_is_in_any_range_inclusive(
    ranges: List[Tuple[int, int]],
) -> ExclusionPredicate:
    """
    Create a function to check whether an input is in any range (inclusive).

    This function should provide reasonable performance
    if queries are mostly made in ascending order.

    Example:
    >>> select = _make_is_in_any_range_inclusive([(3,3), (5,7)])
    >>> select(0)
    False
    >>> select(6)
    True
    >>> [x for x in range(10) if select(x)]
    [3, 5, 6, 7]
    """

    # values are likely queried in ascending order,
    # allowing the search to start with the first possible range
    ranges = sorted(ranges)
    hint_value = 0
    hint_index = 0

    def is_in_any_range(value: int) -> bool:
        nonlocal hint_value, hint_index

        # if the heuristic failed, restart search from the beginning
        if value < hint_value:
            hint_index = 0

        hint_value = value

        for i in range(hint_index, len(ranges)):
            start, end = ranges[i]
            hint_index = i

            # stop as soon as a too-large range is seen
            if value < start:
                break

            if start <= value <= end:
                return True
        else:
            hint_index = len(ranges)

        return False

    return is_in_any_range


def _lines_from_sparse(sparse: Iterable[Tuple[int, str]]) -> List[str]:
    """
    Convert lineno–source tuples to a flat list, useful for tests.

    >>> _lines_from_sparse([(3, 'foo'), (2, 'bar'), (3, 'foo2')])
    ['', 'bar', 'foo2']
    """
    lines: List[str] = []
    for lineno, source in sparse:
        lines.extend("" for _ in range(len(lines), lineno))
        lines[lineno - 1] = source
    return lines
