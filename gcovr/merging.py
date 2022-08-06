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
  so that ``merge(a, empty)`` and ``merge(emtpy, a)`` and ``a`` all match.
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

from dataclasses import dataclass
from typing import Callable, Optional, TypeVar, Dict
from .coverage import (
    BranchCoverage,
    CovData,
    DecisionCoverage,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    DecisionCoverageUncheckable,
    FileCoverage,
    FunctionCoverage,
    LineCoverage,
)


@dataclass
class MergeOptions:
    ignore_function_lineno: bool = False


DEFAULT_MERGE_OPTIONS = MergeOptions()


_Key = TypeVar("_Key", int, str)
_T = TypeVar("_T")


def _merge_dict(
    left: Dict[_Key, _T],
    right: Dict[_Key, _T],
    merge_item: Callable[[_T, _T, MergeOptions], _T],
    options: MergeOptions,
) -> Dict[_Key, _T]:
    """
    Helper function to merge items in a dictionary.

    Example:
    >>> _merge_dict(dict(a=2, b=3), dict(b=1, c=5),
    ...             lambda a, b, _: a + b,
    ...             DEFAULT_MERGE_OPTIONS)
    {'a': 2, 'b': 4, 'c': 5}
    """
    # Ensure that "left" is the larger dict,
    # so that fewer items have to be checked for merging.
    if len(left) < len(right):
        left, right = right, left

    for key, right_item in right.items():
        _insert_coverage_item(left, key, right_item, merge_item, options)

    # At this point, "left" contains all merged items.
    # The caller should access neither the "left" nor "right" objects.
    # While we can't prevent use of the "left" object since we want to return it,
    # we can clear the contents of the "right" object.
    right.clear()

    return left


def _insert_coverage_item(
    target_dict: Dict[_Key, _T],
    key: _Key,
    new_item: _T,
    merge_item: Callable[[_T, _T, MergeOptions], _T],
    options: MergeOptions,
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
        merged_item = merge_item(target_dict[key], new_item, options)
    else:
        merged_item = new_item
    target_dict[key] = merged_item
    return merged_item


def merge_covdata(
    left: CovData, right: CovData, options: MergeOptions = DEFAULT_MERGE_OPTIONS
) -> CovData:
    """
    Merge CovData information.

    Do not use 'left' or 'right' objects afterwards!
    """
    return _merge_dict(left, right, merge_file, options)


def insert_file_coverage(
    target: CovData,
    file: FileCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> FileCoverage:
    """Insert FileCoverage into CovData."""
    return _insert_coverage_item(target, file.filename, file, merge_file, options)


def merge_file(
    left: FileCoverage,
    right: FileCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> FileCoverage:
    """
    Merge FileCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects have same filename.
    """

    assert left.filename == right.filename

    left.lines = _merge_dict(left.lines, right.lines, merge_line, options)
    left.functions = _merge_dict(
        left.functions, right.functions, merge_function, options
    )

    return left


def insert_line_coverage(
    target: FileCoverage,
    line: LineCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> LineCoverage:
    """Insert LineCoverage into FileCoverage."""
    return _insert_coverage_item(target.lines, line.lineno, line, merge_line, options)


# FIXME: use of this function is almost always a bug
def get_or_create_line_coverage(target: FileCoverage, lineno: int) -> LineCoverage:
    """Get the LineCoverage object for that line, or insert a new one if necessary.

    Use of this function is almost always a bug,
    but it's needed for migration.

    The function is almost equivalent to::

        insert_line_coverage(target, LineCoverage(lineno))

    except that this function is guaranteed to not affect the ``noncode`` status
    if any is present.
    """
    try:
        return target.lines[lineno]
    except KeyError:
        target.lines[lineno] = new_line = LineCoverage(lineno)
        return new_line


def merge_line(
    left: LineCoverage,
    right: LineCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> LineCoverage:
    """
    Merge LineCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects must have same lineno.
    """
    assert left.lineno == right.lineno

    left.count += right.count
    # FIXME LineCoverage(lineno) is not the neutral element
    # because the default is "noncode=False", which can flip the other argument to "&"
    left.noncode &= right.noncode
    left.excluded |= right.excluded
    left.branches = _merge_dict(left.branches, right.branches, merge_branch, options)
    left.decision = merge_decision(left.decision, right.decision, options)

    return left


def insert_function_coverage(
    target: FileCoverage,
    function: FunctionCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> FunctionCoverage:
    """Insert FunctionCoverage into FileCoverage"""
    return _insert_coverage_item(
        target.functions, function.name, function, merge_function, options
    )


def merge_function(
    left: FunctionCoverage,
    right: FunctionCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> FunctionCoverage:
    """
    Merge FunctionCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects must have same name and lineno.

    If ``options.ignore_function_lineno`` is set,
    the two function coverage objects can have differing line numbers.
    """
    assert left.name == right.name
    if not options.ignore_function_lineno:
        assert left.lineno == right.lineno

    left.count += right.count

    if options.ignore_function_lineno:
        left.lineno = max(left.lineno, right.lineno)

    return left


def insert_branch_coverage(
    target: LineCoverage,
    branch_id: int,
    branch: BranchCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> BranchCoverage:
    """Insert BranchCoverage into LineCoverage."""
    return _insert_coverage_item(
        target.branches, branch_id, branch, merge_branch, options
    )


def merge_branch(
    left: BranchCoverage,
    right: BranchCoverage,
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> BranchCoverage:
    """
    Merge BranchCoverage information.

    Do not use 'left' or 'right' objects afterwards!
    """

    left.count += right.count
    left.fallthrough |= right.fallthrough
    left.throw |= right.throw

    return left


def insert_decision_coverage(
    target: LineCoverage,
    decision: Optional[DecisionCoverage],
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
) -> Optional[DecisionCoverage]:
    """Insert DecisionCoverage into LineCoverage."""
    target.decision = merge_decision(target.decision, decision)
    return target.decision


def merge_decision(
    left: Optional[DecisionCoverage],
    right: Optional[DecisionCoverage],
    options: MergeOptions = DEFAULT_MERGE_OPTIONS,
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
