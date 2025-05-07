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
The gcovr coverage data model.

This module represents the core data structures
and should not have dependencies on any other gcovr module,
also not on the gcovr.utils module.

The data model should contain the exact same information
as the JSON input/output format.

The types ending with ``*Coverage``
contain per-project/-line/-decision/-branch coverage.

The types ``SummarizedStats``, ``CoverageStat``, and ``DecisionCoverageStat``
report aggregated metrics/percentages.


Merge coverage data.

All of these merging function have the signature
``merge(T, T, MergeOptions) -> T``.
That is, they take two coverage data items and combine them,
returning the combined coverage.
This may change the input objects, so that they should not be used afterwards.

In a mathematical sense, all of these ``merge()`` functions
must behave somewhat like an addition operator:

* commutative: order of arguments must not matter,
  so that ``merge(a, b)`` must match ``merge(b, a)``.
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

from __future__ import annotations
from abc import abstractmethod
import logging
import os
import re
from typing import Any, Callable, List, NoReturn, Optional, TypeVar, Union

from ..filter import is_file_excluded

from ..utils import force_unix_separator
from ..options import Options

from .coverage_dict import (
    BranchesKeyType,
    ConditionsKeyType,
    CallsKeyType,
    CoverageDict,
    LinesKeyType,
)
from .merging import DEFAULT_MERGE_OPTIONS, MergeOptions
from .stats import CoverageStat, DecisionCoverageStat, SummarizedStats

LOGGER = logging.getLogger("gcovr")

GCOVR_DATA_SOURCES = "gcovr/data_sources"
GCOVR_EXCLUDED = "gcovr/excluded"

_T = TypeVar("_T")


class GcovrDataAssertionError(AssertionError):
    """Exception for data merge errors."""


class GcovrMergeAssertionError(AssertionError):
    """Exception for data merge errors."""


def _presentable_filename(filename: str, root_filter: re.Pattern[str]) -> str:
    """Mangle a filename so that it is suitable for a report."""

    normalized = root_filter.sub("", filename)
    if filename.endswith(normalized):
        # remove any slashes between the removed prefix and the normalized name
        if filename != normalized:
            while normalized.startswith(os.path.sep):
                normalized = normalized[len(os.path.sep) :]
    else:
        # Do no truncation if the filter does not start matching
        # at the beginning of the string
        normalized = filename

    return force_unix_separator(normalized)


class CoverageBase:
    """Base class for coverage information."""

    __slots__ = ("data_sources",)

    def __init__(
        self, data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]]
    ) -> None:
        if isinstance(data_source, str):
            self.data_sources = set[tuple[str, ...]]([(data_source,)])
        elif isinstance(data_source, tuple):
            self.data_sources = set[tuple[str, ...]]([data_source])
        else:
            self.data_sources = data_source

    def raise_merge_error(self, msg: str, other: Any) -> NoReturn:
        """Get the exception with message extended with context."""
        location = self.location
        raise GcovrMergeAssertionError(
            "\n".join(
                [
                    msg if location is None else f"{location} {msg}",
                    "GCOV data file of merge source is:"
                    if len(other.data_sources) == 1
                    else "GCOV data files of merge source are:",
                    *[f"   {' -> '.join(e)}" for e in sorted(other.data_sources)],
                    f"and of merge target {'is' if len(self.data_sources) == 1 else 'are'}:",
                    *[f"   {' -> '.join(e)}" for e in sorted(self.data_sources)],
                ]
            )
        )

    def raise_data_error(self, msg: str) -> NoReturn:
        """Get the exception with message extended with context."""
        location = self.location
        raise GcovrDataAssertionError(
            "\n".join(
                [
                    msg if location is None else f"{location} {msg}",
                    f"GCOV data file{' is' if len(self.data_sources) == 1 else 's are'} of merge source:",
                    *[f"   {' -> '.join(e)}" for e in sorted(self.data_sources)],
                ]
            )
        )

    def _merge_property(
        self,
        other: CoverageBase,
        msg: str,
        getter: Callable[[CoverageBase], _T],
    ) -> _T:
        """Assert that the property given by name is defined the same if defined twice. Return the value of the property."""

        left = getter(self)
        right = getter(other)
        if left is not None and right is not None:
            if left != right:
                self.raise_merge_error(
                    f"{msg} must be equal, got {left} and {right}.",
                    other,
                )

        return left or right

    @property
    @abstractmethod
    def key(self) -> Any:
        """Get the key used for the dictionary to unique identify the coverage object."""

    @property
    @abstractmethod
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""


class BranchCoverage(CoverageBase):
    r"""Represent coverage information about a branch.

    Args:
        branchno (int):
            The branch number.
        count (int):
            Number of times this branch was followed.
        fallthrough (bool, optional):
            Whether this is a fallthrough branch. False if unknown.
        throw (bool, optional):
            Whether this is an exception-handling branch. False if unknown.
        source_block_id (int, optional):
            The block number.
        destination_block_id (int, optional):
            The destination block of the branch. None if unknown.
        excluded (bool, optional):
            Whether the branch is excluded.
    """

    first_undefined_source_block_id: bool = True

    __slots__ = (
        "parent",
        "branchno",
        "count",
        "fallthrough",
        "throw",
        "source_block_id",
        "destination_block_id",
        "excluded",
    )

    def __init__(
        self,
        parent: LineCoverage,
        data_source: Union[str, set[tuple[str, ...]]],
        *,
        branchno: int,
        count: int,
        fallthrough: bool = False,
        throw: bool = False,
        source_block_id: Optional[int] = None,
        destination_block_id: Optional[int] = None,
        excluded: bool = False,
    ) -> None:
        super().__init__(data_source)
        self.parent = parent
        if count < 0:
            self.raise_data_error("count must not be a negative value.")

        self.branchno = branchno
        self.count = count
        self.fallthrough = fallthrough
        self.throw = throw
        self.source_block_id = source_block_id
        self.destination_block_id = destination_block_id
        self.excluded = excluded

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize the object."""
        data_dict = dict[str, Any]()
        data_dict.update(
            {
                "count": self.count,
                "fallthrough": self.fallthrough,
                "throw": self.throw,
            }
        )
        if self.source_block_id is not None:
            data_dict["source_block_id"] = self.source_block_id
        if self.destination_block_id is not None:
            data_dict["destination_block_id"] = self.destination_block_id
        if self.excluded:
            data_dict[GCOVR_EXCLUDED] = True
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls,
        linecov: LineCoverage,
        data_source: str,
        branchno: int,
        data_dict: dict[str, Any],
    ) -> BranchCoverage:
        """Deserialize the object."""
        return linecov.insert_branch_coverage(
            data_dict.get(GCOVR_DATA_SOURCES, data_source),
            branchno=branchno,
            count=data_dict["count"],
            source_block_id=data_dict.get("source_block_id"),
            fallthrough=data_dict["fallthrough"],
            throw=data_dict["throw"],
            destination_block_id=data_dict.get("destination_block_id"),
            excluded=data_dict.get(GCOVR_EXCLUDED, False),
        )

    def merge(
        self,
        other: BranchCoverage,
        _option: MergeOptions,
    ) -> None:
        """
        Merge BranchCoverage information.

        Do not use 'other' objects afterwards!

            Examples:
        >>> filecov = FileCoverage("file.gcov", filename="file.cpp")
        >>> linecov = LineCoverage(filecov, "line.gcov", lineno=100, count=2, function_name="function")
        >>> left = BranchCoverage(linecov, "left.gcov", branchno=0, count=1, source_block_id=2)
        >>> right = BranchCoverage(linecov, "right.gcov", branchno=0, count=1, source_block_id=3)
        >>> left.merge(right, DEFAULT_MERGE_OPTIONS)
        Traceback (most recent call last):
          ...
        gcovr.data_model.coverage.GcovrMergeAssertionError: file.cpp:100 (branch 0) Source block ID must be equal, got 2 and 3.
        GCOV data file of merge source is:
           right.gcov
        and of merge target is:
           left.gcov
        >>> left = BranchCoverage(..., "left.gcov", branchno=0, count=1, source_block_id=2)
        >>> right = BranchCoverage(..., "right.gcov", branchno=0, count=4, source_block_id=2, fallthrough=False, throw=True)
        >>> right.excluded = True
        >>> left.merge(right, DEFAULT_MERGE_OPTIONS)
        >>> left.count
        5
        >>> left.fallthrough
        False
        >>> left.throw
        True
        >>> left.excluded
        True
        """

        self.count += other.count
        self.fallthrough |= other.fallthrough
        self.throw |= other.throw
        self.source_block_id = self._merge_property(
            other, "Source block ID", lambda x: x.source_block_id
        )
        self.destination_block_id = self._merge_property(
            other, "Destination block ID", lambda x: x.destination_block_id
        )
        self.excluded |= other.excluded

    @property
    def key(self) -> BranchesKeyType:
        """Get the key used for the dictionary to unique identify the coverage object."""
        return (
            self.branchno,
            self.source_block_id or 0,
            self.destination_block_id or 0,
        )

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return f"{self.parent.location} (branch {self.branchno})"

    @property
    def source_block_id_or_0(self) -> int:
        """Get a valid block number (0) if there was no definition in GCOV file."""
        if self.source_block_id is None:
            self.source_block_id = 0
            if BranchCoverage.first_undefined_source_block_id:
                BranchCoverage.first_undefined_source_block_id = False
                LOGGER.info("No block number defined, assuming 0 for all undefined")

        return self.source_block_id

    @property
    def is_excluded(self) -> bool:
        """Return True if the branch is excluded."""
        return self.excluded

    @property
    def is_reportable(self) -> bool:
        """Return True if the branch is reportable."""
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        """Return True if the branch is covered."""
        return self.is_reportable and self.count > 0


class ConditionCoverage(CoverageBase):
    r"""Represent coverage information about a condition.

    Args:
        conditionno (int):
            The number of the condition.
        count (int):
            Number of condition outcomes in this expression.
        covered (int):
            Number of covered condition outcomes in this expression.
        not_covered_true list[int]:
            The conditions which were not true.
        not_covered_false list[int]:
            The conditions which were not false.
        excluded (bool, optional):
            Whether the condition is excluded.
    """

    __slots__ = (
        "parent",
        "conditionno",
        "count",
        "covered",
        "not_covered_true",
        "not_covered_false",
        "excluded",
    )

    def __init__(
        self,
        parent: LineCoverage,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        conditionno: int,
        count: int,
        covered: int,
        not_covered_true: list[int],
        not_covered_false: list[int],
        excluded: bool = False,
    ) -> None:
        super().__init__(data_source)
        self.parent = parent
        if count < 0:
            self.raise_data_error("count must not be a negative value.")
        if count < covered:
            self.raise_data_error("count must not be less than covered.")

        self.conditionno = conditionno
        self.count = count
        self.covered = covered
        self.not_covered_true = not_covered_true
        self.not_covered_false = not_covered_false
        self.excluded = excluded

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize the object."""
        data_dict = {
            "count": self.count,
            "covered": self.covered,
            "not_covered_false": self.not_covered_false,
            "not_covered_true": self.not_covered_true,
        }
        if self.excluded:
            data_dict[GCOVR_EXCLUDED] = True
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls,
        linecov: LineCoverage,
        data_source: str,
        conditionno: int,
        data_dict: dict[str, Any],
    ) -> ConditionCoverage:
        """Deserialize the object."""
        return linecov.insert_condition_coverage(
            data_dict.get(GCOVR_DATA_SOURCES, data_source),
            conditionno=conditionno,
            count=data_dict["count"],
            covered=data_dict["covered"],
            not_covered_false=data_dict["not_covered_false"],
            not_covered_true=data_dict["not_covered_true"],
            excluded=data_dict.get(GCOVR_EXCLUDED, False),
        )

    def merge(
        self,
        other: ConditionCoverage,
        _option: MergeOptions,
    ) -> None:
        """
        Merge ConditionCoverage information.

        Do not use 'other' objects afterwards!

        Examples:
        >>> filecov = FileCoverage("file.gcov", filename="file.c")
        >>> linecov = LineCoverage(filecov, "line.gcov", lineno=10, count=2, function_name="function")
        >>> left = ConditionCoverage(linecov, "left.gcov", conditionno=1, count=4, covered=2, not_covered_true=[1, 2], not_covered_false=[])
        >>> right = ConditionCoverage(linecov, "right.gcov", conditionno=2, count=4, covered=2, not_covered_true=[2], not_covered_false=[1, 3])
        >>> left.merge(right, DEFAULT_MERGE_OPTIONS)
        Traceback (most recent call last):
          ...
        gcovr.data_model.coverage.GcovrMergeAssertionError: file.c:10 (condition 1) The condition number must be equal, got 2 and expected 1.
        GCOV data file of merge source is:
           right.gcov
        and of merge target is:
           left.gcov
        >>> left = ConditionCoverage(linecov, "left.gcov", conditionno=1, count=4, covered=2, not_covered_true=[1, 2], not_covered_false=[])
        >>> right = ConditionCoverage(linecov, "right.gcov", conditionno=1, count=4, covered=2, not_covered_true=[2], not_covered_false=[1, 3], excluded=True)
        >>> left.merge(right, DEFAULT_MERGE_OPTIONS)
        >>> left.count
        4
        >>> left.covered
        3
        >>> left.not_covered_true
        [2]
        >>> left.not_covered_false
        []
        >>> left.excluded
        True
        """
        if self.conditionno != other.conditionno:
            self.raise_merge_error(
                f"The condition number must be equal, got {other.conditionno} and expected {self.conditionno}.",
                other,
            )
        if self.count != other.count:
            self.raise_merge_error(
                f"The number of conditions must be equal, got {other.count} and expected {self.count}.",
                other,
            )

        self.not_covered_false = sorted(
            list(set(self.not_covered_false) & set(other.not_covered_false))
        )
        self.not_covered_true = sorted(
            list(set(self.not_covered_true) & set(other.not_covered_true))
        )
        self.covered = (
            self.count - len(self.not_covered_false) - len(self.not_covered_true)
        )
        self.excluded |= other.excluded

    @property
    def key(self) -> ConditionsKeyType:
        """Get the key used for the dictionary to unique identify the coverage object."""
        return (self.conditionno, self.count)

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return f"{self.parent.location} (condition {self.conditionno})"

    @property
    def is_excluded(self) -> bool:
        """Return True if the branch is excluded."""
        return self.excluded

    @property
    def is_reportable(self) -> bool:
        """Return True if the branch is reportable."""
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        """Return True if the condition is covered."""
        return self.is_reportable and self.covered > 0

    @property
    def is_fully_covered(self) -> bool:
        """Return True if the condition is covered."""
        return self.is_reportable and self.covered == self.count


class DecisionCoverageUncheckable(CoverageBase):
    r"""Represent coverage information about a decision."""

    __slots__ = ("parent",)

    def __init__(
        self,
        parent: Optional[LineCoverage],
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
    ) -> None:
        super().__init__(data_source)
        self.parent = parent

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize the object."""
        data_dict = dict[str, Any]({"type": "uncheckable"})
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls, linecov: LineCoverage, data_source: str, data_dict: dict[str, Any]
    ) -> None:
        """Deserialize the object."""
        linecov.insert_decision_coverage(
            DecisionCoverageUncheckable(
                linecov, data_dict.get(GCOVR_DATA_SOURCES, data_source)
            )
        )

    def merge(self, other: DecisionCoverageUncheckable) -> None:
        """Merge the decision coverage."""

    @property
    def key(self) -> NoReturn:
        """Get the key used for the dictionary to unique identify the coverage object."""
        raise NotImplementedError("Function not implemented for decision objects.")

    @property
    def location(self) -> Optional[str]:
        """Get a string defining the source location for the coverage data."""
        return None if self.parent is None else self.parent.location

    @property
    def is_covered(self) -> bool:
        """Return true if the decision is covered."""
        return True

    def coverage(self) -> DecisionCoverageStat:
        """Get the coverage stat."""
        return DecisionCoverageStat(0, 1, 2)  # TODO should it be uncheckable=2?


class DecisionCoverageConditional(CoverageBase):
    r"""Represent coverage information about a decision.

    Args:
        count_true (int):
            Number of times this decision was made.

        count_false (int):
            Number of times this decision was made.

    """

    __slots__ = "parent", "count_true", "count_false"

    def __init__(
        self,
        parent: Optional[LineCoverage],
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        count_true: int,
        count_false: int,
    ) -> None:
        super().__init__(data_source)
        self.parent = parent
        if count_true < 0:
            self.raise_data_error("count_true must not be a negative value.")
        self.count_true = count_true
        if count_false < 0:
            self.raise_data_error("count_true must not be a negative value.")
        self.count_false = count_false

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize the object."""
        data_dict = dict[str, Any](
            {
                "type": "conditional",
                "count_true": self.count_true,
                "count_false": self.count_false,
            }
        )
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls, linecov: LineCoverage, data_source: str, data_dict: dict[str, Any]
    ) -> None:
        """Deserialize the object."""
        linecov.insert_decision_coverage(
            DecisionCoverageConditional(
                linecov,
                data_dict.get(GCOVR_DATA_SOURCES, data_source),
                count_true=data_dict["count_true"],
                count_false=data_dict["count_false"],
            )
        )

    def merge(self, other: DecisionCoverageConditional) -> None:
        """Merge the decision coverage."""
        self.count_true += other.count_true
        self.count_false += other.count_false

    @property
    def key(self) -> NoReturn:
        """Get the key used for the dictionary to unique identify the coverage object."""
        raise NotImplementedError("Function not implemented for decision objects.")

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return None if self.parent is None else self.parent.location

    @property
    def is_covered(self) -> bool:
        """Return true if the decision is covered."""
        return not (self.count_true == 0 or self.count_false == 0)

    def coverage(self) -> DecisionCoverageStat:
        """Get the coverage stat."""
        covered = 0
        if self.count_true > 0:
            covered += 1
        if self.count_false > 0:
            covered += 1
        return DecisionCoverageStat(covered, 0, 2)


class DecisionCoverageSwitch(CoverageBase):
    r"""Represent coverage information about a decision.

    Args:
        count (int):
            Number of times this decision was made.
    """

    __slots__ = "parent", "count"

    def __init__(
        self,
        parent: Optional[LineCoverage],
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        count: int,
    ) -> None:
        super().__init__(data_source)
        self.parent = parent
        if count < 0:
            self.raise_data_error("count must not be a negative value.")
        self.count = count

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize the object."""
        data_dict = dict[str, Any](
            {
                "type": "switch",
                "count": self.count,
            }
        )
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls, linecov: LineCoverage, data_source: str, data_dict: dict[str, Any]
    ) -> None:
        """Deserialize the object."""
        linecov.insert_decision_coverage(
            DecisionCoverageSwitch(
                linecov,
                data_dict.get(GCOVR_DATA_SOURCES, data_source),
                count=data_dict["count"],
            )
        )

    def merge(self, other: DecisionCoverageSwitch) -> None:
        """Merge the decision coverage."""
        self.count += other.count

    @property
    def key(self) -> NoReturn:
        """Get the key used for the dictionary to unique identify the coverage object."""
        raise NotImplementedError("Function not implemented for decision objects.")

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return None if self.parent is None else self.parent.location

    @property
    def is_covered(self) -> bool:
        """Return true if the decision is covered."""
        return self.count != 0

    def coverage(self) -> DecisionCoverageStat:
        """Get the coverage stat."""
        covered = 0
        if self.count > 0:
            covered += 1
        return DecisionCoverageStat(covered, 0, 1)


DecisionCoverage = Union[
    DecisionCoverageUncheckable,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
]


class CallCoverage(CoverageBase):
    r"""Represent coverage information about a call.

    Args:
        callno (int):
            The number of the call.
        source_block_id (int):
            The block number.
        destination_block_id (int, optional):
            The destination block of the branch. None if unknown.
        returned (int):
            How often the function call returned.
        excluded (bool, optional):
            Whether the call is excluded.
    """

    __slots__ = (
        "parent",
        "callno",
        "source_block_id",
        "destination_block_id",
        "returned",
        "excluded",
    )

    def __init__(
        self,
        parent: LineCoverage,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        callno: int,
        source_block_id: int,
        destination_block_id: Optional[int],
        returned: int,
        excluded: bool = False,
    ) -> None:
        super().__init__(data_source)
        self.parent = parent
        self.callno = callno
        self.source_block_id = source_block_id
        self.destination_block_id = destination_block_id
        self.returned = returned
        self.excluded = excluded

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize the object."""
        data_dict = dict[str, Any](
            {
                "source_block_id": self.source_block_id,
            }
        )
        if self.destination_block_id is not None:
            data_dict["destination_block_id"] = self.destination_block_id
        data_dict["returned"] = self.returned
        if self.excluded:
            data_dict[GCOVR_EXCLUDED] = True
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls,
        linecov: LineCoverage,
        data_source: str,
        callno: int,
        data_dict: dict[str, Any],
    ) -> CallCoverage:
        """Deserialize the object."""
        return linecov.insert_call_coverage(
            data_dict.get(GCOVR_DATA_SOURCES, data_source),
            callno=callno,
            returned=data_dict["returned"],
            source_block_id=data_dict["source_block_id"],
            destination_block_id=data_dict.get("destination_block_id"),
            excluded=data_dict.get(GCOVR_EXCLUDED, False),
        )

    def merge(
        self,
        other: CallCoverage,
        _option: MergeOptions,
    ) -> CallCoverage:
        """
        Merge CallCoverage information.

        Do not use 'left' or 'right' objects afterwards!
        """
        if self.callno != other.callno:
            self.raise_data_error(
                f"Call number must be equal, got {self.callno} and {other.callno}."
            )
        self.returned += other.returned
        self.source_block_id = self._merge_property(
            other, "Source block ID", lambda x: x.source_block_id
        )
        self.destination_block_id = self._merge_property(
            other, "Destination block ID", lambda x: x.destination_block_id
        )
        self.excluded |= other.excluded

        return self

    @property
    def key(self) -> CallsKeyType:
        """Get the key used for the dictionary to unique identify the coverage object."""
        return self.callno

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return f"{self.parent.location} (call {self.callno})"

    @property
    def is_excluded(self) -> bool:
        """Return True if the call is excluded."""
        return self.excluded

    @property
    def is_reportable(self) -> bool:
        """Return True if the call is reportable."""
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        """Return True if the call is covered."""
        return self.is_reportable and self.returned != 0


class LineCoverage(CoverageBase):
    r"""Represent coverage information about a line.

    Each line is either *excluded* or *reportable*.

    A *reportable* line is either *covered* or *uncovered*.

    The default state of a line is *coverable*/*reportable*/*uncovered*.

    Args:
        lineno (int):
            The line number.
        count (int):
            How often this line was executed at least partially.
        function_name (str):
            Mangled name of the function the line belongs to.
        block_ids (*int, optional):
            List of block ids in this line
        excluded (bool, optional):
            Whether this line is excluded by a marker.
        md5 (str, optional):
            The md5 checksum of the source code line.
    """

    __slots__ = (
        "parent",
        "lineno",
        "count",
        "function_name",
        "block_ids",
        "excluded",
        "md5",
        "branches",
        "conditions",
        "decision",
        "calls",
    )

    def __init__(
        self,
        parent: FileCoverage,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        lineno: int,
        count: int,
        function_name: Optional[str],
        block_ids: Optional[list[int]] = None,
        md5: Optional[str] = None,
        excluded: bool = False,
    ) -> None:
        super().__init__(data_source)
        self.parent = parent
        if lineno <= 0:
            self.raise_data_error("Line number must be a positive value.")
        if count < 0:
            self.raise_data_error("count must not be a negative value.")

        self.lineno = lineno
        self.count = count
        self.function_name = function_name
        self.block_ids = block_ids
        self.md5 = md5
        self.excluded = excluded
        self.branches = CoverageDict[BranchesKeyType, BranchCoverage]()
        self.conditions = CoverageDict[ConditionsKeyType, ConditionCoverage]()
        self.decision: Optional[DecisionCoverage] = None
        self.calls = CoverageDict[CallsKeyType, CallCoverage]()

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> dict[str, Any]:
        """Serialize the object."""
        data_dict = dict[str, Any](
            {
                "line_number": self.lineno,
            }
        )
        if self.function_name is not None:
            data_dict["function_name"] = self.function_name

        if self.block_ids is not None:
            data_dict["block_ids"] = self.block_ids

        data_dict.update(
            {
                "count": self.count,
                "branches": [
                    branchcov.serialize(get_data_source)
                    for _, branchcov in sorted(self.branches.items())
                ],
            }
        )
        if self.conditions:
            data_dict["conditions"] = [
                conditioncov.serialize(get_data_source)
                for _, conditioncov in sorted(self.conditions.items())
            ]
        if self.decision is not None:
            data_dict["gcovr/decision"] = self.decision.serialize(get_data_source)
        if len(self.calls) > 0:
            data_dict["calls"] = [
                callcov.serialize(get_data_source)
                for _, callcov in sorted(self.calls.items())
            ]
        if self.md5:
            data_dict["gcovr/md5"] = self.md5
        if self.excluded:
            data_dict[GCOVR_EXCLUDED] = True
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls,
        filecov: FileCoverage,
        data_source: str,
        data_dict: dict[str, Any],
    ) -> LineCoverage:
        """Deserialize the object."""
        linecov = filecov.insert_line_coverage(
            data_dict.get(GCOVR_DATA_SOURCES, data_source),
            lineno=data_dict["line_number"],
            count=data_dict["count"],
            function_name=data_dict.get("function_name"),
            block_ids=data_dict.get("block_ids"),
            md5=data_dict.get("gcovr/md5"),
            excluded=data_dict.get(GCOVR_EXCLUDED, False),
        )

        for branchno, data_dict_branch in enumerate(data_dict["branches"]):
            BranchCoverage.deserialize(linecov, data_source, branchno, data_dict_branch)

        if (conditions := data_dict.get("conditions")) is not None:
            for conditionno, data_dict_condition in enumerate(conditions):
                ConditionCoverage.deserialize(
                    linecov, data_source, conditionno, data_dict_condition
                )

        if (data_dict_decision := data_dict.get("gcovr/decision")) is not None:
            decision_type = data_dict_decision["type"]
            if decision_type == "uncheckable":
                DecisionCoverageUncheckable.deserialize(
                    linecov, data_source, data_dict_decision
                )
            elif decision_type == "conditional":
                DecisionCoverageConditional.deserialize(
                    linecov, data_source, data_dict_decision
                )
            elif decision_type == "switch":
                DecisionCoverageSwitch.deserialize(
                    linecov, data_source, data_dict_decision
                )
            else:
                raise AssertionError(f"Unknown decision type: {decision_type!r}")

        if (calls := data_dict.get("calls")) is not None:
            for callno, data_dict_call in enumerate(calls):
                CallCoverage.deserialize(linecov, data_source, callno, data_dict_call)
        return linecov

    def merge(
        self,
        other: LineCoverage,
        options: MergeOptions,
    ) -> LineCoverage:
        """
        Merge LineCoverage information.

        Do not use 'left' or 'right' objects afterwards!

        Precondition: both objects must have same lineno.
        """
        if self.lineno != other.lineno:
            self.raise_merge_error("Line number must be equal.", other)
        if self.function_name != other.function_name:
            self.raise_merge_error("Function name must be equal.", other)
        self.md5 = self._merge_property(other, "MD5 checksum", lambda x: x.md5)

        self.count += other.count
        self.excluded |= other.excluded
        self.branches.merge(other.branches, options)
        self.conditions.merge(other.conditions, options)
        self.__merge_decision(other.decision)
        self.calls.merge(other.calls, options)

        return self

    def __merge_decision(  # pylint: disable=too-many-return-statements
        self,
        decisioncov: Optional[DecisionCoverage],
    ) -> None:
        """Merge DecisionCoverage information.

        The DecisionCoverage has different states:

        - None (no known decision)
        - Uncheckable (there was a decision, but it can't be analyzed properly)
        - Conditional
        - Switch

        If there is a conflict between different types, Uncheckable will be returned.
        """
        # If decision coverage is not known for one side, return the other.
        if self.decision is not None and decisioncov is not None:
            # If the type is different the result is Uncheckable.
            if type(self.decision) is type(decisioncov):
                self.decision.merge(decisioncov)  # type: ignore [arg-type]
            else:
                self.decision = DecisionCoverageUncheckable(
                    self,
                    set[tuple[str, ...]](
                        *self.decision.data_sources, *decisioncov.data_sources
                    ),
                )
        elif self.decision is None:
            self.decision = decisioncov

    def insert_branch_coverage(
        self,
        data_source: Union[str, set[tuple[str, ...]]],
        *,
        branchno: int,
        count: int,
        fallthrough: bool = False,
        throw: bool = False,
        source_block_id: Optional[int] = None,
        destination_block_id: Optional[int] = None,
        excluded: bool = False,
    ) -> BranchCoverage:
        """Add a branch coverage item, merge if needed."""
        branchcov = BranchCoverage(
            self,
            data_source,
            branchno=branchno,
            count=count,
            fallthrough=fallthrough,
            throw=throw,
            source_block_id=source_block_id,
            destination_block_id=destination_block_id,
            excluded=excluded,
        )
        key = branchcov.key
        if key in self.branches:
            self.branches[key].merge(branchcov, DEFAULT_MERGE_OPTIONS)
        else:
            self.branches[key] = branchcov
            self.branches[key].parent = self

        return branchcov

    def insert_condition_coverage(
        self,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        conditionno: int,
        count: int,
        covered: int,
        not_covered_true: list[int],
        not_covered_false: list[int],
        excluded: bool = False,
    ) -> ConditionCoverage:
        """Add a condition coverage item, merge if needed."""
        conditioncov = ConditionCoverage(
            self,
            data_source=data_source,
            conditionno=conditionno,
            count=count,
            covered=covered,
            not_covered_true=not_covered_true,
            not_covered_false=not_covered_false,
            excluded=excluded,
        )
        key = conditioncov.key
        if key in self.conditions:
            self.conditions[key].merge(conditioncov, DEFAULT_MERGE_OPTIONS)
        else:
            self.conditions[key] = conditioncov
            self.conditions[key].parent = self

        return conditioncov

    def insert_decision_coverage(
        self,
        decisioncov: Optional[DecisionCoverage],
    ) -> None:
        """Add a condition coverage item, merge if needed."""
        self.__merge_decision(decisioncov)
        if self.decision is not None:
            self.decision.parent = self

    def insert_call_coverage(
        self,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        callno: int,
        source_block_id: int,
        destination_block_id: Optional[int],
        returned: int,
        excluded: bool = False,
    ) -> CallCoverage:
        """Add a branch coverage item, merge if needed."""
        callcov = CallCoverage(
            self,
            data_source=data_source,
            callno=callno,
            source_block_id=source_block_id,
            destination_block_id=destination_block_id,
            returned=returned,
            excluded=excluded,
        )
        key = callcov.key
        if key in self.calls:
            self.calls[key].merge(callcov, DEFAULT_MERGE_OPTIONS)
        else:
            self.calls[key] = callcov
            self.calls[key].parent = self

        return callcov

    @property
    def key(self) -> LinesKeyType:
        """Get the key used for the dictionary to unique identify the coverage object."""
        return (self.lineno, "" if self.function_name is None else self.function_name)

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return f"{self.parent.location}:{self.lineno}"

    @property
    def is_excluded(self) -> bool:
        """Return True if the line is excluded."""
        return self.excluded

    @property
    def is_reportable(self) -> bool:
        """Return True if the line is reportable."""
        return not self.excluded

    @property
    def is_covered(self) -> bool:
        """Return True if the line is covered."""
        return self.is_reportable and self.count > 0

    @property
    def is_uncovered(self) -> bool:
        """Return True if the line is uncovered."""
        return self.is_reportable and self.count == 0

    @property
    def has_uncovered_branch(self) -> bool:
        """Return True if the line has a uncovered branches."""
        return not all(
            branchcov.is_covered or branchcov.is_excluded
            for branchcov in self.branches.values()
        )

    @property
    def has_uncovered_decision(self) -> bool:
        """Return True if the line has a uncovered decision."""
        if self.decision is None:
            return False

        return not self.decision.is_covered

    def exclude(self) -> None:
        """Exclude line from coverage statistic."""
        self.excluded = True
        self.count = 0
        self.branches.clear()
        self.conditions.clear()
        self.decision = None
        self.calls.clear()

    def branch_coverage(self) -> CoverageStat:
        """Return the branch coverage statistic of the line."""
        total = 0
        covered = 0
        for branchcov in self.branches.values():
            if branchcov.is_reportable:
                total += 1
                if branchcov.is_covered:
                    covered += 1
        return CoverageStat(covered=covered, total=total)

    def condition_coverage(self) -> CoverageStat:
        """Return the condition coverage statistic of the line."""
        total = 0
        covered = 0
        for condition in self.conditions.values():
            if condition.is_reportable:
                total += condition.count
                covered += condition.covered
        return CoverageStat(covered=covered, total=total)

    def decision_coverage(self) -> DecisionCoverageStat:
        """Return the decision coverage statistic of the line."""
        if self.decision is None:
            return DecisionCoverageStat(0, 0, 0)

        return self.decision.coverage()


class FunctionCoverage(CoverageBase):
    r"""Represent coverage information about a function.

    The counter is stored as dictionary with the line as key to be able
    to merge function coverage in different ways

    Args:
        mangled_name (str):
            The mangled name of the function. If demangled_name is None and
            the name contains a brace it's used as demangled_name. This is needed
            to support existing GCOV text output where we do not know if the
            option --demanglednames was used for generation. If it contains a brace
            the demangled name must be None.
        demangled_name (str):
            The demangled name of the functions.
        lineno (int):
            The line number.
        count (int):
            How often this function was executed.
        blocks (float):
            Block coverage of function.
        start ((int, int)), optional):
            Tuple with function start line and column.
        end ((int, int)), optional):
            Tuple with function end line and column.
        excluded (bool, optional):
            Whether this line is excluded by a marker.
    """

    __slots__ = (
        "parent",
        "mangled_name",
        "demangled_name",
        "count",
        "blocks",
        "start",
        "end",
        "excluded",
    )

    def __init__(
        self,
        parent: FileCoverage,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        mangled_name: Optional[str],
        demangled_name: Optional[str],
        lineno: int,
        count: int,
        blocks: float,
        start: Optional[tuple[int, int]] = None,
        end: Optional[tuple[int, int]] = None,
        excluded: bool = False,
    ) -> None:
        super().__init__(data_source)
        self.parent = parent

        if count < 0:
            self.raise_data_error("count must not be a negative value.")
        if mangled_name is not None:
            # We have a demangled name as name -> demangled_name must be None and we need to change the values
            if "(" in mangled_name:
                if demangled_name is not None:
                    self.raise_data_error(
                        f"If 'name' contains a demangled name (got '{mangled_name}') the 'demangled_name' must be None (got {demangled_name})."
                    )
                mangled_name, demangled_name = (None, mangled_name)

        self.mangled_name = mangled_name
        self.demangled_name = demangled_name
        self.count = CoverageDict[int, int]({lineno: count})
        self.blocks = CoverageDict[int, float]({lineno: blocks})
        self.excluded = CoverageDict[int, bool]({lineno: excluded})
        self.start: Optional[CoverageDict[int, tuple[int, int]]] = (
            None
            if start is None
            else CoverageDict[int, tuple[int, int]]({lineno: start})
        )
        self.end: Optional[CoverageDict[int, tuple[int, int]]] = (
            None if end is None else CoverageDict[int, tuple[int, int]]({lineno: end})
        )

    def serialize(
        self,
        get_data_source: Callable[[CoverageBase], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Serialize the object."""
        data_dict_list = list[dict[str, Any]]()
        for lineno, count in self.count.items():
            data_dict = dict[str, Any]()
            if self.mangled_name is not None:
                data_dict["name"] = self.mangled_name
            if self.demangled_name is not None:
                data_dict["demangled_name"] = self.demangled_name
            data_dict.update(
                {
                    "lineno": lineno,
                    "execution_count": count,
                    "blocks_percent": self.blocks[lineno],
                }
            )
            if self.start is not None and self.end is not None:
                data_dict["pos"] = (
                    ":".join([str(e) for e in self.start[lineno]]),
                    ":".join([str(e) for e in self.end[lineno]]),
                )
            if self.excluded[lineno]:
                data_dict[GCOVR_EXCLUDED] = True
            data_dict.update(get_data_source(self))
            data_dict_list.append(data_dict)

        return data_dict_list

    @classmethod
    def deserialize(
        cls,
        filecov: FileCoverage,
        merge_options: MergeOptions,
        data_source: str,
        data_dict: dict[str, Any],
    ) -> FunctionCoverage:
        """Deserialize the object."""
        start: Optional[tuple[int, int]] = None
        end: Optional[tuple[int, int]] = None
        if "pos" in data_dict:
            start_l_c = data_dict["pos"][0].split(":", maxsplit=1)
            start = (int(start_l_c[0]), int(start_l_c[1]))
            end_l_c = data_dict["pos"][1].split(":", maxsplit=1)
            end = (int(end_l_c[0]), int(end_l_c[1]))

        return filecov.insert_function_coverage(
            data_dict.get(GCOVR_DATA_SOURCES, data_source),
            merge_options,
            mangled_name=data_dict.get("name"),
            demangled_name=data_dict.get("demangled_name"),
            lineno=data_dict["lineno"],
            count=data_dict["execution_count"],
            blocks=data_dict["blocks_percent"],
            start=start,
            end=end,
            excluded=data_dict.get(GCOVR_EXCLUDED, False),
        )

    def merge(
        self,
        other: FunctionCoverage,
        options: MergeOptions,
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
        self.demangled_name = self._merge_property(
            other, "Function demangled name", lambda x: x.demangled_name
        )
        # If we have a demangled name use the first mangled name
        # For virtual constructors/destructors several mangled functions map to the same demangled name,
        # see https://itanium-cxx-abi.github.io/cxx-abi/abi.html#mangling-special-ctor-dtor:
        # <ctor-dtor-name> ::= C1                     # complete object constructor
        #                  ::= C2                     # base object constructor
        #                  ::= C3                     # complete object allocating constructor
        #                  ::= CI1 <base class type>  # complete object inheriting constructor
        #                  ::= CI2 <base class type>  # base object inheriting constructor
        #                  ::= D0                     # deleting destructor
        #                  ::= D1                     # complete object destructor
        #                  ::= D2                     # base object destructor
        if self.demangled_name is not None:
            if self.mangled_name is None:
                self.mangled_name = other.mangled_name
            elif (
                other.mangled_name is not None
                and other.mangled_name < self.mangled_name
            ):
                self.mangled_name = other.mangled_name
        # If we do not have mangled names the mangled name must be the same.
        else:
            self.mangled_name = self._merge_property(
                other, "Function mangled name", lambda x: x.mangled_name
            )
        if not options.func_opts.ignore_function_lineno:
            if self.count.keys() != other.count.keys():
                lines = sorted(set([*self.count.keys(), *other.count.keys()]))
                self.raise_merge_error(
                    f"Got function {self.name} on multiple lines: {', '.join([str(line) for line in lines])}.\n"
                    "\tYou can run gcovr with --merge-mode-functions=MERGE_MODE.\n"
                    "\tThe available values for MERGE_MODE are described in the documentation.",
                    other,
                )

        # keep distinct counts for each line number
        if options.func_opts.separate_function:
            for lineno, count in sorted(other.count.items()):
                try:
                    self.count[lineno] += count
                except KeyError:
                    self.count[lineno] = count
            for lineno, blocks in other.blocks.items():
                try:
                    # Take the maximum value for this line
                    if self.blocks[lineno] < blocks:
                        self.blocks[lineno] = blocks
                except KeyError:
                    self.blocks[lineno] = blocks
            for lineno, excluded in other.excluded.items():
                try:
                    self.excluded[lineno] |= excluded
                except KeyError:
                    self.excluded[lineno] = excluded
            if other.start is not None:
                if self.start is None:
                    self.start = CoverageDict[int, tuple[int, int]]()
                for lineno, start in other.start.items():
                    self.start[lineno] = start
            if other.end is not None:
                if self.end is None:
                    self.end = CoverageDict[int, tuple[int, int]]()
                for lineno, end in other.end.items():
                    self.end[lineno] = end
            return self

        right_lineno = list(other.count.keys())[0]
        # merge all counts into an entry for a single line number
        if right_lineno in self.count:
            lineno = right_lineno
        elif options.func_opts.merge_function_use_line_zero:
            lineno = 0
        elif options.func_opts.merge_function_use_line_min:
            lineno = min(*self.count.keys(), *other.count.keys())
        elif options.func_opts.merge_function_use_line_max:
            lineno = max(*self.count.keys(), *other.count.keys())
        else:
            raise AssertionError("Sanity check, unknown merge mode")

        # Overwrite data with the sum at the desired line
        self.count = CoverageDict[int, int](
            {lineno: sum(self.count.values()) + sum(other.count.values())}
        )
        # or the max value at the desired line
        self.blocks = CoverageDict[int, float](
            {lineno: max(*self.blocks.values(), *other.blocks.values())}
        )
        # or the logical or of all values
        self.excluded = CoverageDict[int, bool](
            {lineno: any(self.excluded.values()) or any(other.excluded.values())}
        )

        if self.start is not None and other.start is not None:
            # or the minimum start
            self.start = CoverageDict[int, tuple[int, int]](
                {lineno: min(*self.start.values(), *other.start.values())}
            )
        if self.end is not None and other.end is not None:
            # or the maximum end
            self.end = CoverageDict[int, tuple[int, int]](
                {lineno: max(*self.end.values(), *other.end.values())}
            )

        return self

    @property
    def key(self) -> str:
        """Get the key for the dict."""
        return self.name

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return f"{self.parent.location} (function {self.name})"

    @property
    def name(self) -> str:
        """Get the function name. This is the demangled name if present, else the mangled name."""
        return str(self.demangled_name or self.mangled_name)

    def is_function(self, name: Optional[str]) -> bool:
        """Is the name one of the function."""
        return name is not None and (name in (self.mangled_name, self.demangled_name))

    @property
    def name_and_signature(self) -> tuple[str, str]:
        """Get a tuple with function name and signature, if signature is un."""
        if self.demangled_name is None:
            return (str(self.name), "")

        if "(" not in self.demangled_name:
            return (str(self.demangled_name), "")

        open_brackets, close_brackets = (0, 0)
        signature = ""
        for part in reversed(self.demangled_name.split("(")):
            signature = f"({part}{signature}"
            open_brackets += 1
            close_brackets += len(re.findall(r"(\))", part))
            if open_brackets == close_brackets:
                break
        else:
            self.raise_data_error(
                f"Can't split function {self.demangled_name!r} into name and signature."
            )

        return (self.demangled_name[: -len(signature)], signature)


class FileCoverage(CoverageBase):
    """Represent coverage information about a file."""

    __slots__ = "filename", "functions", "lines", "lines_keys_by_lineno"

    def __init__(
        self,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        *,
        filename: str,
    ) -> None:
        super().__init__(data_source)
        self.filename: str = filename
        self.functions = CoverageDict[str, FunctionCoverage]()
        self.lines = CoverageDict[LinesKeyType, LineCoverage]()
        self.lines_keys_by_lineno: dict[int, List[LinesKeyType]] = {}

    def presentable_filename(self, root_filter: re.Pattern[str]) -> str:
        """Mangle a filename so that it is suitable for a report."""
        return _presentable_filename(self.filename, root_filter)

    def merge(
        self,
        other: FileCoverage,
        options: MergeOptions,
    ) -> None:
        """
        Merge FileCoverage information.

        Do not use 'other' objects afterwards!

        Precondition: both objects have same filename.
        """

        if self.filename != other.filename:
            self.raise_data_error("Filename must be equal")

        self.lines.merge(other.lines, options)
        self.functions.merge(other.functions, options)
        if other.data_sources:
            self.data_sources.update(other.data_sources)

    def serialize(self, options: Options) -> dict[str, Any]:
        """Serialize the object."""
        # Only write data in verbose mode
        if options.verbose:

            def get_data_source(cov: CoverageBase) -> dict[str, Any]:
                """Return the printable data sources."""
                return {
                    GCOVR_DATA_SOURCES: [
                        [
                            _presentable_filename(filename, options.root_filter)
                            for filename in data_source
                        ]
                        for data_source in sorted(cov.data_sources)
                    ]
                }
        else:

            def get_data_source(cov: CoverageBase) -> dict[str, Any]:  # pylint: disable=unused-argument
                """Stub if not running in verbose mode."""
                return {}

        filename = self.presentable_filename(options.root_filter)
        if options.json_base:
            filename = "/".join([options.json_base, filename])
        data_dict = {
            "file": filename,
            "lines": [
                line.serialize(get_data_source)
                for _, line in sorted(self.lines.items())
            ],
            "functions": [
                f
                for _, function in sorted(self.functions.items())
                for f in function.serialize(get_data_source)
            ],
        }
        data_dict.update(get_data_source(self))

        return data_dict

    @classmethod
    def deserialize(
        cls,
        data_source: str,
        data_dict: dict[str, Any],
        merge_options: MergeOptions,
        options: Options,
    ) -> Optional[FileCoverage]:
        """Deserialize the object."""
        filename = os.path.join(
            os.path.abspath(options.root), os.path.normpath(data_dict["file"])
        )

        if is_file_excluded(filename, options.filter, options.exclude):
            return None

        filecov = FileCoverage(
            data_dict.get(GCOVR_DATA_SOURCES, data_source),
            filename=filename,
        )
        for data_dict_function in data_dict["functions"]:
            FunctionCoverage.deserialize(
                filecov, merge_options, data_source, data_dict_function
            )
        for data_dict_line in data_dict["lines"]:
            LineCoverage.deserialize(filecov, data_source, data_dict_line)

        return filecov

    @property
    def key(self) -> NoReturn:
        """Get the key used for the dictionary to unique identify the coverage object."""
        raise NotImplementedError(
            "Function not implemented for file coverage object, use property 'filename' instead."
        )

    @property
    def location(self) -> Optional[str]:
        """Get the source location of the coverage data."""
        return self.filename

    @property
    def stats(self) -> SummarizedStats:
        """Create a coverage statistic of a file coverage object."""
        return SummarizedStats(
            line=self.line_coverage(),
            branch=self.branch_coverage(),
            condition=self.condition_coverage(),
            decision=self.decision_coverage(),
            function=self.function_coverage(),
            call=self.call_coverage(),
        )

    def insert_line_coverage(
        self,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        options: MergeOptions = DEFAULT_MERGE_OPTIONS,
        *,
        lineno: int,
        count: int,
        function_name: Optional[str],
        block_ids: Optional[list[int]] = None,
        md5: Optional[str] = None,
        excluded: bool = False,
    ) -> LineCoverage:
        """Add a line coverage item, merge if needed."""
        linecov = LineCoverage(
            self,
            data_source,
            lineno=lineno,
            count=count,
            function_name=function_name,
            block_ids=block_ids,
            md5=md5,
            excluded=excluded,
        )
        key = linecov.key
        if key in self.lines:
            self.lines[key].merge(linecov, options)
        else:
            self.lines[key] = linecov
            self.lines[key].parent = self
            if linecov.lineno not in self.lines_keys_by_lineno:
                self.lines_keys_by_lineno[linecov.lineno] = []
            self.lines_keys_by_lineno[linecov.lineno].append(key)

        return self.lines[key]

    def insert_function_coverage(
        self,
        data_source: Union[str, tuple[str, ...], set[tuple[str, ...]]],
        options: MergeOptions = DEFAULT_MERGE_OPTIONS,
        *,
        mangled_name: Optional[str],
        demangled_name: Optional[str],
        lineno: int,
        count: int,
        blocks: float,
        start: Optional[tuple[int, int]] = None,
        end: Optional[tuple[int, int]] = None,
        excluded: bool = False,
    ) -> FunctionCoverage:
        """Add a function coverage item, merge if needed."""
        functioncov = FunctionCoverage(
            self,
            data_source,
            mangled_name=mangled_name,
            demangled_name=demangled_name,
            lineno=lineno,
            count=count,
            blocks=blocks,
            start=start,
            end=end,
            excluded=excluded,
        )
        key = functioncov.key
        if key in self.functions:
            self.functions[key].merge(functioncov, options)
        else:
            self.functions[key] = functioncov
            self.functions[key].parent = self

        return functioncov

    def filter_for_function(self, functioncov: FunctionCoverage) -> FileCoverage:
        """Get a file coverage object reduced to a single function"""
        if functioncov.key not in self.functions:
            self.raise_data_error(
                f"Function {functioncov.key} must be in filtered file coverage object."
            )
        filecov = FileCoverage(self.data_sources, filename=self.filename)
        filecov.functions[functioncov.key] = functioncov

        filecov.lines = CoverageDict[tuple[int, str], LineCoverage](
            {
                key: linecov
                for key, linecov in self.lines.items()
                if functioncov.is_function(linecov.function_name)
            }
        )

        return filecov

    def function_coverage(self) -> CoverageStat:
        """Return the function coverage statistic of the file."""
        total = 0
        covered = 0

        for functioncov in self.functions.values():
            for lineno, excluded in functioncov.excluded.items():
                if not excluded:
                    total += 1
                    if functioncov.count[lineno] > 0:
                        covered += 1

        return CoverageStat(covered, total)

    def line_coverage(self) -> CoverageStat:
        """Return the line coverage statistic of the file."""
        total = 0
        covered = 0

        for linecov in self.lines.values():
            if linecov.is_reportable:
                total += 1
                if linecov.is_covered:
                    covered += 1

        return CoverageStat(covered, total)

    def branch_coverage(self) -> CoverageStat:
        """Return the branch coverage statistic of the file."""
        stat = CoverageStat.new_empty()

        for linecov in self.lines.values():
            if linecov.is_reportable:
                stat += linecov.branch_coverage()

        return stat

    def condition_coverage(self) -> CoverageStat:
        """Return the condition coverage statistic of the file."""
        stat = CoverageStat.new_empty()

        for linecov in self.lines.values():
            if linecov.is_reportable:
                stat += linecov.condition_coverage()

        return stat

    def decision_coverage(self) -> DecisionCoverageStat:
        """Return the decision coverage statistic of the file."""
        stat = DecisionCoverageStat.new_empty()

        for linecov in self.lines.values():
            if linecov.is_reportable:
                stat += linecov.decision_coverage()

        return stat

    def call_coverage(self) -> CoverageStat:
        """Return the call coverage statistic of the file."""
        covered = 0
        total = 0

        for linecov in self.lines.values():
            if linecov.is_reportable and len(linecov.calls) > 0:
                for callcov in linecov.calls.values():
                    if callcov.is_reportable:
                        total += 1
                        if callcov.is_covered:
                            covered += 1

        return CoverageStat(covered, total)
