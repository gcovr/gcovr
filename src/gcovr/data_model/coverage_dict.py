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

from __future__ import annotations
import logging
from typing import Optional, TypeVar

from .merging import MergeOptions

LOGGER = logging.getLogger("gcovr")

LinesKeyType = tuple[int, str]
BranchesKeyType = tuple[Optional[int], Optional[int], Optional[int]]
ConditionsKeyType = tuple[int, int]
CallsKeyType = tuple[Optional[int], int, Optional[int]]
_Key = TypeVar(
    "_Key", int, str, LinesKeyType, BranchesKeyType, ConditionsKeyType, CallsKeyType
)
_T = TypeVar("_T")


class CoverageDict(dict[_Key, _T]):
    """Base class for a coverage dictionary."""

    def merge(
        self,
        other: CoverageDict[_Key, _T],
        options: MergeOptions,
    ) -> None:
        """Helper function to merge items in a dictionary."""

        # Ensure that "self" is the larger dict,
        # so that fewer items have to be checked for merging.
        # FIXME: This needs to be changed, result should be independent of the order
        if len(self) < len(other):
            other.merge(self, options)
            for key, item in other.items():
                self[key] = item
        else:
            for key, item in other.items():
                if key in self:
                    self[key].merge(item, options)
                else:
                    self[key] = item

        # At this point, "self" contains all merged items.
        # The caller should access "other" objects therefore we clear it.
        other.clear()
