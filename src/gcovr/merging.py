# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.3
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

"""
Merge coverage data.

All of these merging function have the signature
``merge(T, T) -> T``.
That is, they take two coverage data items and combine them,
returning the combined coverage.
This may change the input objects, so that they should be used afterwards.

In a mathematical sense, all of these ``merge()`` functions
must behave somewhat like an addition operator:

* commutative: order of arguments must not matter,
  so that ``merge(a, b)`` must match ``merge(a, b)``.
* associative: order of merging must not matter,
  so that ``merge(a, merge(b, c))`` must match ``merge(merge(a, b), c)``.
* identity element: there must be an empty element,
  so that ``merge(a, empty)`` and ``merge(empty, a)`` and ``a`` all match.
  However, the empty state might be implied by “parent dict does not contain an entry”,
  or must contain matching information like the same line number.

The insertion functions insert a single coverage item into a larger structure,
for example inserting BranchCoverage into a LineCoverage object.
The target/parent structure is updated in-place,
otherwise this has equivalent semantics to merging.
In particular, if there already is coverage data in the target with the same ID,
then the contents are merged.
The insertion functions return the coverage structure that is saved in the target,
which may not be the same as the input value.
"""

from dataclasses import dataclass, field
import logging
from typing import Callable, Optional, TypeVar

from .options import Options
from .coverage import (
    BranchCoverage,
    ConditionCoverage,
    CoverageContainer,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
    CallCoverage,
)


LOGGER = logging.getLogger("gcovr")


class GcovrMergeAssertionError(AssertionError):
    """Exception for data merge errors."""


@dataclass
class MergeFunctionOptions:
    """Data class to store the function merge options."""

    ignore_function_lineno: bool = False
    merge_function_use_line_zero: bool = False
    merge_function_use_line_min: bool = False
    merge_function_use_line_max: bool = False
    separate_function: bool = False


FUNCTION_STRICT_MERGE_OPTIONS = MergeFunctionOptions()
FUNCTION_LINE_ZERO_MERGE_OPTIONS = MergeFunctionOptions(
    ignore_function_lineno=True,
    merge_function_use_line_zero=True,
)
FUNCTION_MIN_LINE_MERGE_OPTIONS = MergeFunctionOptions(
    ignore_function_lineno=True,
    merge_function_use_line_min=True,
)
FUNCTION_MAX_LINE_MERGE_OPTIONS = MergeFunctionOptions(
    ignore_function_lineno=True,
    merge_function_use_line_max=True,
)
SEPARATE_FUNCTION_MERGE_OPTIONS = MergeFunctionOptions(
    ignore_function_lineno=True,
    separate_function=True,
)


@dataclass
class MergeConditionOptions:
    """Data class to store the condition merge options."""

    merge_condition_fold: bool = False


CONDITION_STRICT_MERGE_OPTIONS = MergeConditionOptions()
CONDITION_FOLD_MERGE_OPTIONS = MergeConditionOptions(
    merge_condition_fold=True,
)


@dataclass
class MergeOptions:
    """Data class to store the merge options."""

    func_opts: MergeFunctionOptions = field(default_factory=MergeFunctionOptions)
    cond_opts: MergeConditionOptions = field(default_factory=MergeConditionOptions)


DEFAULT_MERGE_OPTIONS = MergeOptions()


def get_merge_mode_from_options(options: Options) -> MergeOptions:
    """Get the function merge mode."""
    merge_opts = MergeOptions()
    if options.merge_mode_functions == "strict":
        merge_opts.func_opts = FUNCTION_STRICT_MERGE_OPTIONS
    elif options.merge_mode_functions == "merge-use-line-0":
        merge_opts.func_opts = FUNCTION_LINE_ZERO_MERGE_OPTIONS
    elif options.merge_mode_functions == "merge-use-line-min":
        merge_opts.func_opts = FUNCTION_MIN_LINE_MERGE_OPTIONS
    elif options.merge_mode_functions == "merge-use-line-max":
        merge_opts.func_opts = FUNCTION_MAX_LINE_MERGE_OPTIONS
    elif options.merge_mode_functions == "separate":
        merge_opts.func_opts = SEPARATE_FUNCTION_MERGE_OPTIONS
    else:
        raise AssertionError("Sanity check: Unknown functions merge mode.")

    if options.merge_mode_conditions == "strict":
        merge_opts.cond_opts = CONDITION_STRICT_MERGE_OPTIONS
    elif options.merge_mode_conditions == "fold":
        merge_opts.cond_opts = CONDITION_FOLD_MERGE_OPTIONS
    else:
        raise AssertionError("Sanity check: Unknown conditions merge mode.")

    return merge_opts


_Key = TypeVar("_Key", int, str)
_T = TypeVar("_T")


def _merge_dict(
    left: dict[_Key, _T],
    right: dict[_Key, _T],
    merge_item: Callable[[_T, _T, MergeOptions, Optional[str]], _T],
    options: MergeOptions,
    context: Optional[str],
) -> dict[_Key, _T]:
    """
    Helper function to merge items in a dictionary.

    Example:
    >>> _merge_dict(dict(a=2, b=3), dict(b=1, c=5),
    ...             lambda a, b, _o, _c: a + b,
    ...             DEFAULT_MERGE_OPTIONS,
    ...             None)
    {'a': 2, 'b': 4, 'c': 5}
    """
    # Ensure that "left" is the larger dict,
    # so that fewer items have to be checked for merging.
    if len(left) < len(right):
        left, right = right, left

    for key, right_item in right.items():
        _insert_coverage_item(left, key, right_item, merge_item, options, context)

    # At this point, "left" contains all merged items.
    # The caller should access neither the "left" nor "right" objects.
    # While we can't prevent use of the "left" object since we want to return it,
    # we can clear the contents of the "right" object.
    right.clear()

    return left


def _insert_coverage_item(
    target_dict: dict[_Key, _T],
    key: _Key,
    new_item: _T,
    merge_item: Callable[[_T, _T, MergeOptions, Optional[str]], _T],
    options: MergeOptions,
    context: Optional[str],
) -> _T:
    """
    Insert a single item into a coverage dictionary.

    That means::

        merge(left, { key: item })

    and::

        insert_coverage_item(left, key, item, ...)

    should be equivalent with respect to their side effects.

    However, the target dict is updated in place,
    and the return value differs!
    """

    if key in target_dict:
        merged_item = merge_item(target_dict[key], new_item, options, context)
    else:
        merged_item = new_item
    target_dict[key] = merged_item
    return merged_item


def merge_covdata(
    left: CoverageContainer, right: CoverageContainer, options: MergeOptions
) -> CoverageContainer:
    """
    Merge CoverageContainer information and clear directory statistics.

    Do not use 'left' or 'right' objects afterwards!
    """
    left.directories.clear()
    right.directories.clear()
    left.data = _merge_dict(left.data, right.data, merge_file, options, None)
    return left


def insert_file_coverage(
    target: CoverageContainer,
    file: FileCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> FileCoverage:
    """Insert FileCoverage into CoverageContainer and clear directory statistics."""
    target.directories.clear()
    return _insert_coverage_item(
        target.data, file.filename, file, merge_file, options, None
    )


def merge_file(
    left: FileCoverage,
    right: FileCoverage,
    options: MergeOptions,
    context: Optional[str],
) -> FileCoverage:
    """
    Merge FileCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects have same filename.
    """

    if left.filename != right.filename:
        raise AssertionError("Filename must be equal")
    if context is not None:
        raise AssertionError("For a file the context must not be set.")

    try:
        left.lines = _merge_dict(
            left.lines, right.lines, merge_line, options, left.filename
        )
        left.functions = _merge_dict(
            left.functions, right.functions, merge_function, options, left.filename
        )
        if right.data_sources:
            left.data_sources.update(right.data_sources)
    except AssertionError as exc:
        message = [str(exc)]
        if right.data_sources:
            message += (
                "GCOV source files of merge source is/are:",
                *[f"\t{e}" for e in sorted(right.data_sources)],
            )
        if left.data_sources:
            message += (
                "and of merge target is/are:",
                *[f"\t{e}" for e in sorted(left.data_sources)],
            )
        raise AssertionError("\n".join(message)) from None

    return left


def insert_line_coverage(
    target: FileCoverage,
    linecov: LineCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> LineCoverage:
    """Insert LineCoverage into FileCoverage."""
    return _insert_coverage_item(
        target.lines, linecov.lineno, linecov, merge_line, options, target.filename
    )


def merge_line(
    left: LineCoverage,
    right: LineCoverage,
    options: MergeOptions,
    context: Optional[str],
) -> LineCoverage:
    """
    Merge LineCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects must have same lineno.
    """
    context = f"{context}:{left.lineno}"
    if left.lineno != right.lineno:
        raise AssertionError("Line number must be equal.")
    # If both checksums exists compare them if only one exists, use it.
    if left.md5 is not None and right.md5 is not None:
        if left.md5 != right.md5:
            raise AssertionError(f"MD5 checksum of {context} must be equal.")
    elif right.md5 is not None:
        left.md5 = right.md5

    left.count += right.count
    left.excluded |= right.excluded
    left.branches = _merge_dict(
        left.branches, right.branches, merge_branch, options, context
    )
    left.conditions = _merge_dict(
        left.conditions, right.conditions, merge_condition, options, context
    )
    left.decision = merge_decision(left.decision, right.decision, options, context)
    left.calls = _merge_dict(left.calls, right.calls, merge_call, options, context)

    return left


def insert_function_coverage(
    filecov: FileCoverage,
    function: FunctionCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> FunctionCoverage:
    """Insert FunctionCoverage into FileCoverage"""
    return _insert_coverage_item(
        filecov.functions,
        function.name or function.demangled_name,
        function,
        merge_function,
        options,
        filecov.filename,
    )


def merge_function(
    left: FunctionCoverage,
    right: FunctionCoverage,
    options: MergeOptions,
    context: Optional[str],
) -> FunctionCoverage:
    """
    Merge FunctionCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects must have same name and lineno.

    If ``options.func_opts.ignore_function_lineno`` is set,
    the two function coverage objects can have differing line numbers.
    With following flags the merge mode can be defined:
      - ``options.func_opts.merge_function_use_line_zero``
      - ``options.func_opts.merge_function_use_line_min``
      - ``options.func_opts.merge_function_use_line_max``
      - ``options.func_opts.separate_function``
    """
    if left.demangled_name != right.demangled_name:
        raise AssertionError("Function demangled name must be equal.")
    if left.name != right.name:
        raise AssertionError("Function name must be equal.")
    if not options.func_opts.ignore_function_lineno:
        if left.count.keys() != right.count.keys():
            lines = sorted(set([*left.count.keys(), *right.count.keys()]))
            raise GcovrMergeAssertionError(
                f"Got function {right.demangled_name} in {context} on multiple lines: {', '.join([str(line) for line in lines])}.\n"
                "\tYou can run gcovr with --merge-mode-functions=MERGE_MODE.\n"
                "\tThe available values for MERGE_MODE are described in the documentation."
            )

    # keep distinct counts for each line number
    if options.func_opts.separate_function:
        for lineno, count in sorted(right.count.items()):
            try:
                left.count[lineno] += count
            except KeyError:
                left.count[lineno] = count
        for lineno, blocks in right.blocks.items():
            try:
                # Take the maximum value for this line
                if left.blocks[lineno] < blocks:
                    left.blocks[lineno] = blocks
            except KeyError:
                left.blocks[lineno] = blocks
        for lineno, excluded in right.excluded.items():
            try:
                left.excluded[lineno] |= excluded
            except KeyError:
                left.excluded[lineno] = excluded
        if right.start is not None:
            if left.start is None:
                left.start = {}
            for lineno, start in right.start.items():
                left.start[lineno] = start
        if right.end is not None:
            if left.end is None:
                left.end = {}
            for lineno, end in right.end.items():
                left.end[lineno] = end
        return left

    right_lineno = list(right.count.keys())[0]
    # merge all counts into an entry for a single line number
    if right_lineno in left.count:
        lineno = right_lineno
    elif options.func_opts.merge_function_use_line_zero:
        lineno = 0
    elif options.func_opts.merge_function_use_line_min:
        lineno = min(*left.count.keys(), *right.count.keys())
    elif options.func_opts.merge_function_use_line_max:
        lineno = max(*left.count.keys(), *right.count.keys())
    else:
        raise AssertionError("Sanity check, unknown merge mode")

    # Overwrite data with the sum at the desired line
    left.count = {lineno: sum(left.count.values()) + sum(right.count.values())}
    # or the max value at the desired line
    left.blocks = {lineno: max(*left.blocks.values(), *right.blocks.values())}
    # or the logical or of all values
    left.excluded = {
        lineno: any(left.excluded.values()) or any(right.excluded.values())
    }

    if left.start is not None and right.start is not None:
        # or the minimum start
        left.start = {lineno: min(*left.start.values(), *right.start.values())}
    if left.end is not None and right.end is not None:
        # or the maximum end
        left.end = {lineno: max(*left.end.values(), *right.end.values())}

    return left


def insert_branch_coverage(
    linecov: LineCoverage,
    branchno: int,
    branchcov: BranchCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> BranchCoverage:
    """Insert BranchCoverage into LineCoverage."""
    return _insert_coverage_item(
        linecov.branches, branchno, branchcov, merge_branch, options, None
    )


def merge_branch(
    left: BranchCoverage,
    right: BranchCoverage,
    _options: MergeOptions,
    _context: Optional[str],
) -> BranchCoverage:
    """
    Merge BranchCoverage information.

    Do not use 'left' or 'right' objects afterwards!

        Examples:
    >>> left = BranchCoverage(1, 2)
    >>> right = BranchCoverage(1, 3, False, True)
    >>> right.excluded = True
    >>> merged = merge_branch(left, right, DEFAULT_MERGE_OPTIONS, None)
    >>> merged.count
    5
    >>> merged.fallthrough
    False
    >>> merged.throw
    True
    >>> merged.excluded
    True
    """

    left.count += right.count
    left.fallthrough |= right.fallthrough
    left.throw |= right.throw
    if left.excluded is True or right.excluded is True:
        left.excluded = True

    return left


def insert_condition_coverage(
    linecov: LineCoverage,
    condition_id: int,
    conditioncov: ConditionCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> ConditionCoverage:
    """Insert ConditionCoverage into LineCoverage."""
    return _insert_coverage_item(
        linecov.conditions, condition_id, conditioncov, merge_condition, options, None
    )


def merge_condition(
    left: ConditionCoverage,
    right: ConditionCoverage,
    options: MergeOptions,
    context: Optional[str],
) -> ConditionCoverage:
    """
    Merge ConditionCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Examples:
    >>> left = ConditionCoverage(4, 2, [1, 2], [])
    >>> right = ConditionCoverage(4, 3, [2], [1, 3])
    >>> merge_condition(left, None, DEFAULT_MERGE_OPTIONS, None) is left
    True
    >>> merge_condition(None, right, DEFAULT_MERGE_OPTIONS, None) is right
    True
    >>> merged = merge_condition(left, right, DEFAULT_MERGE_OPTIONS, None)
    >>> merged.count
    4
    >>> merged.covered
    3
    >>> merged.not_covered_true
    [2]
    >>> merged.not_covered_false
    []

    If ``options.cond_opts.merge_condition_fold`` is set,
    the two condition coverage lists can have differing counts.
    The conditions are shrunk to match the lowest count
    """

    # If condition coverage is not know for one side, return the other.
    if left is None:
        return right
    if right is None:
        return left

    if left.count != right.count:
        if options.cond_opts.merge_condition_fold:
            LOGGER.warning(
                f"Condition counts are not equal, got {right.count} and expected {left.count}. "
                f"Reducing to {min(left.count, right.count)}."
            )
            if left.count > right.count:
                left.not_covered_true = left.not_covered_true[
                    : len(right.not_covered_true)
                ]
                left.not_covered_false = left.not_covered_false[
                    : len(right.not_covered_false)
                ]
                left.count = right.count
            else:
                right.not_covered_true = right.not_covered_true[
                    : len(left.not_covered_true)
                ]
                right.not_covered_false = right.not_covered_false[
                    : len(left.not_covered_false)
                ]
                right.count = left.count
        else:
            raise AssertionError(
                f"The number of conditions must be equal, got {right.count} and expected {left.count} while merging {context}.\n"
                "\tYou can run gcovr with --merge-mode-conditions=MERGE_MODE.\n"
                "\tThe available values for MERGE_MODE are described in the documentation."
            )

    left.not_covered_false = sorted(
        list(set(left.not_covered_false) & set(right.not_covered_false))
    )
    left.not_covered_true = sorted(
        list(set(left.not_covered_true) & set(right.not_covered_true))
    )
    left.covered = left.count - len(left.not_covered_false) - len(left.not_covered_true)

    return left


def insert_decision_coverage(
    target: LineCoverage,
    decision: Optional[DecisionCoverage],
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> Optional[DecisionCoverage]:
    """Insert DecisionCoverage into LineCoverage."""
    target.decision = merge_decision(target.decision, decision, options, None)
    return target.decision


def merge_decision(  # pylint: disable=too-many-return-statements
    left: Optional[DecisionCoverage],
    right: Optional[DecisionCoverage],
    _options: MergeOptions,
    _context: Optional[str],
) -> Optional[DecisionCoverage]:
    """
    Merge DecisionCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    The DecisionCoverage has different states:

    - None (no known decision)
    - Uncheckable (there was a decision, but it can't be analyzed properly)
    - Conditional
    - Switch

    If there is a conflict between different types, Uncheckable will be returned.
    """

    # The DecisionCoverage classes have long names, so abbreviate them here:
    Conditional = DecisionCoverageConditional
    Switch = DecisionCoverageSwitch
    Uncheckable = DecisionCoverageUncheckable

    # If decision coverage is not know for one side, return the other.
    if left is None:
        return right
    if right is None:
        return left

    # If any decision is Uncheckable, the result is Uncheckable.
    if isinstance(left, Uncheckable):
        return left
    if isinstance(right, Uncheckable):
        return right

    # Merge Conditional decisions.
    if isinstance(left, Conditional) and isinstance(right, Conditional):
        left.count_true += right.count_true
        left.count_false += right.count_false
        return left

    # Merge Switch decisions.
    if isinstance(left, Switch) and isinstance(right, Switch):
        left.count += right.count
        return left

    # If the decisions have conflicting types, the result is Uncheckable.
    return Uncheckable()


def insert_call_coverage(
    target: LineCoverage,
    call: CallCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> CallCoverage:
    """Insert BranchCoverage into LineCoverage."""
    return _insert_coverage_item(
        target.calls, call.callno, call, merge_call, options, None
    )


def merge_call(
    left: CallCoverage,
    right: CallCoverage,
    _options: MergeOptions,
    context: Optional[str],
) -> CallCoverage:
    """
    Merge CallCoverage information.

    Do not use 'left' or 'right' objects afterwards!
    """
    if left.callno != right.callno:
        raise AssertionError(
            f"Call number must be equal, got {left.callno} and {right.callno} while merging {context}."
        )
    left.covered |= right.covered
    return left
