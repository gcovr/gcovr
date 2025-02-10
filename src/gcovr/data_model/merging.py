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

from ..options import Options


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
