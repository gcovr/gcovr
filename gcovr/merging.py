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
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
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
"""

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


_Key = TypeVar("_Key", int, str)
_T = TypeVar("_T")


def _merge_dict(
    left: Dict[_Key, _T],
    right: Dict[_Key, _T],
    merge_item: Callable[[_T, _T], _T],
) -> Dict[_Key, _T]:
    """
    Helper function to merge items in a dictionary.

    Example:
    >>> _merge_dict(dict(a=2, b=3), dict(b=1, c=5), lambda a, b: a + b)
    {'a': 2, 'b': 4, 'c': 5}
    """
    # ensure that "left" is the larger dict
    if len(left) < len(right):
        left, right = right, left

    for key, right_item in right.items():
        if key in left:
            left[key] = merge_item(left[key], right_item)
        else:
            left[key] = right_item
    return left


def merge_covdata(left: CovData, right: CovData) -> CovData:
    """
    Merge CovData information.

    Do not use 'left' or 'right' objects afterwards!
    """
    return _merge_dict(left, right, merge_file)


def merge_file(left: FileCoverage, right: FileCoverage) -> FileCoverage:
    """
    Merge FileCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects have same filename.
    """

    assert left.filename == right.filename

    left.lines = _merge_dict(left.lines, right.lines, merge_line)
    left.functions = _merge_dict(left.functions, right.functions, merge_function)

    return left


def merge_line(left: LineCoverage, right: LineCoverage) -> LineCoverage:
    """
    Merge LineCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects must have same lineno.
    """
    assert left.lineno == right.lineno

    left.count += right.count
    left.noncode &= right.noncode
    left.excluded |= right.excluded
    left.branches = _merge_dict(left.branches, right.branches, merge_branch)
    left.decision = merge_decision(left.decision, right.decision)

    return left


def merge_function(left: FunctionCoverage, right: FunctionCoverage) -> FunctionCoverage:
    """
    Merge FunctionCoverage information.

    Do not use 'left' or 'right' objects afterwards!

    Precondition: both objects must have same name and lineno.
    """
    assert left.name == right.name
    assert left.lineno == right.lineno

    left.count += right.count

    return left


def merge_branch(left: BranchCoverage, right: BranchCoverage) -> BranchCoverage:
    """
    Merge BranchCoverage information.

    Do not use 'left' or 'right' objects afterwards!
    """

    left.count += right.count
    left.fallthrough = left.fallthrough or right.fallthrough
    left.throw = left.throw or right.throw

    return left


def merge_decision(
    left: Optional[DecisionCoverage], right: Optional[DecisionCoverage]
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

    # If decision coverage is not know for one side, return the other.
    if left is None:
        return right
    if right is None:
        return left

    # If any decision is Uncheckable, the result is Uncheckable.
    if isinstance(left, DecisionCoverageUncheckable):
        return left
    if isinstance(right, DecisionCoverageUncheckable):
        return right

    # Merge Conditional decisions.
    Conditional = DecisionCoverageConditional
    if isinstance(left, Conditional) and isinstance(right, Conditional):
        left.count_true += right.count_true
        left.count_false += right.count_false
        return left

    # Merge Switch decisions.
    Switch = DecisionCoverageSwitch
    if isinstance(left, Switch) and isinstance(right, Switch):
        left.count += right.count
        return left

    # If the decisions have conflicting types, the result is Uncheckable.
    return DecisionCoverageUncheckable()
