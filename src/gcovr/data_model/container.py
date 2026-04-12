# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from __future__ import annotations
import os
import re
from typing import Any, Iterator, Literal, ValuesView, overload

from ..filter import is_file_excluded
from ..logging import LOGGER
from ..options import Options
from ..utils import commonpath, force_unix_separator

from .coverage import FileCoverage
from .coverage_dict import CoverageDict
from .merging import MergeOptions
from .stats import CoverageStat, DecisionCoverageStat, SummarizedStats


class CoverageContainer:
    """Coverage container holding all the coverage data."""

    def __init__(self, dirname: str, parent: CoverageContainer | None = None) -> None:
        self.data = CoverageDict[str, CoverageContainer | FileCoverage]()
        self.dirname = os.path.abspath(dirname) + os.path.sep
        self.parent = parent
        self._properties = dict[str, Any]()
        self._stats: SummarizedStats | None = None

    def __getitem__(self, key: str) -> CoverageContainer | FileCoverage:
        return self.data[key]

    def __setitem__(
        self, key: str, value: CoverageContainer | FileCoverage
    ) -> CoverageContainer | FileCoverage:
        self.data[key] = value
        return value

    def __delitem__(self, key: str) -> None:
        del self.data[key]

    def __len__(self) -> int:
        return len(self.data)

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def clear(
        self,
    ) -> None:
        """Clear the file coverage data."""
        self.data.clear()

    def values(self) -> ValuesView[CoverageContainer | FileCoverage]:
        """Get the file coverage data objects."""
        return self.data.values()

    def filecov(self, recurse: bool = False) -> Iterator[FileCoverage]:
        """Get the file coverage data objects."""
        for value in self.values():
            if isinstance(value, FileCoverage):
                yield value
            elif recurse:
                yield from value.filecov(recurse=True)

    def dircov(self, recurse: bool = False) -> Iterator[CoverageContainer]:
        """Get the directory coverage data objects."""
        for value in self.values():
            if isinstance(value, CoverageContainer):
                if recurse:
                    yield from value.dircov(recurse=True)
        yield self

    def traverse(self) -> Iterator[CoverageContainer | FileCoverage]:
        """Traverse the coverage data object tree."""
        for value in self.values():
            if isinstance(value, FileCoverage):
                yield value
            else:
                yield from value.traverse()
        yield self

    def remove_container_with_single_item(self) -> None:
        """Remove directory containers with only one file coverage item."""
        # Iterate over a copy of the values to avoid modifying the dictionary while iterating
        for value in list(self.values()):
            if isinstance(value, CoverageContainer):
                value.remove_container_with_single_item()

        children = list(self.values())
        if len(children) == 1:
            child = children[0]
            if isinstance(child, FileCoverage):
                if self.parent is not None:
                    LOGGER.debug(
                        "   Move file %s to directory %s. %s",
                        child.filename,
                        self.parent.dirname,
                        list(self.parent.data.keys()),
                    )
                    del self.parent[self.dirname]
                    self.parent[child.filename] = child
            else:
                self.clear()
                LOGGER.debug(
                    "   Move content of %s to directory %s.",
                    child.dirname,
                    self.dirname,
                )
                for child_covdata in child.values():
                    if isinstance(child_covdata, FileCoverage):
                        LOGGER.debug("      Move file %s.", child_covdata.filename)
                        self[child_covdata.filename] = child_covdata
                    else:
                        LOGGER.debug("      Move directory %s.", child_covdata.dirname)
                        self[child_covdata.dirname] = child_covdata
                        child_covdata.parent = self

    def serialize(self, options: Options) -> list[dict[str, Any]]:
        """Serialize the object."""
        data = list[dict[str, Any]]()
        for value in sorted(self.filecov(recurse=True), key=lambda cov: cov.filename):
            data.append(value.serialize(options))
        return data

    @classmethod
    def deserialize(
        cls,
        data_sources: str,
        data_dicts_files: list[dict[str, Any]],
        options: Options,
        merge_options: MergeOptions,
    ) -> CoverageContainer:
        """Serialize the object."""
        covdata = CoverageContainer(options.root)
        for gcovr_file in data_dicts_files:
            if (
                filecov := FileCoverage.deserialize(
                    data_sources, gcovr_file, merge_options, options
                )
            ) is not None:
                covdata.insert_file_coverage(
                    filecov,
                    merge_options,
                )
        return covdata

    def is_compare_info_available(self) -> bool:
        """Check weather the data has compare information or not."""
        return any(
            filecov.is_compare_info_available()
            for filecov in self.filecov(recurse=True)
        )

    @overload
    @classmethod
    def __sorted(
        cls,
        covdata_list: list[FileCoverage],
        sort_key: Literal["filename", "uncovered-number", "uncovered-percent"],
        sort_reverse: bool,
        by_metric: Literal["line", "branch", "decision"],
        filename_uses_relative_pathname: bool,
    ) -> list[FileCoverage]:
        """Sort a list of FileCoverage objects."""

    @overload
    @classmethod
    def __sorted(
        cls,
        covdata_list: list[CoverageContainer],
        sort_key: Literal["filename", "uncovered-number", "uncovered-percent"],
        sort_reverse: bool,
        by_metric: Literal["line", "branch", "decision"],
        filename_uses_relative_pathname: bool,
    ) -> list[CoverageContainer]:
        """Sort a list of CoverageContainer objects."""

    @overload
    @classmethod
    def __sorted(
        cls,
        covdata_list: list[FileCoverage | CoverageContainer],
        sort_key: Literal["filename", "uncovered-number", "uncovered-percent"],
        sort_reverse: bool,
        by_metric: Literal["line", "branch", "decision"],
        filename_uses_relative_pathname: bool,
    ) -> list[FileCoverage | CoverageContainer]:
        """Sort a list of FileCoverage objects."""

    @classmethod
    def __sorted(
        cls,
        covdata_list: list[FileCoverage]
        | list[CoverageContainer]
        | list[FileCoverage | CoverageContainer],
        sort_key: Literal["filename", "uncovered-number", "uncovered-percent"],
        sort_reverse: bool,
        by_metric: Literal["line", "branch", "decision"],
        filename_uses_relative_pathname: bool,
    ) -> (
        list[FileCoverage]
        | list[CoverageContainer]
        | list[FileCoverage | CoverageContainer]
    ):
        """Sort a coverage dict.

        covdata_list (list[CoverageContainer | FileCoverage]): The coverage list
        sort_key ("filename", "uncovered-number", "uncovered-percent"): The values to sort by
        sort_reverse (bool): Reverse order if True
        by_metric ("line", "branch", "decision"): Select the metric to sort
        filename_uses_relative_pathname (bool): For HTML, we break down a pathname to the
            relative path, but not for other formats.

        returns: the sorted keys
        """

        basedir = commonpath([covdata.filename for covdata in covdata_list])

        def key_filename(covdata: CoverageContainer | FileCoverage) -> list[int | str]:
            def convert_to_int_if_possible(text: str) -> int | str:
                return int(text) if text.isdigit() else text

            key = (
                force_unix_separator(
                    os.path.relpath(
                        os.path.realpath(covdata.filename), os.path.realpath(basedir)
                    )
                )
                if filename_uses_relative_pathname
                else covdata.filename
            ).casefold()

            return [
                convert_to_int_if_possible(part) for part in re.split(r"([0-9]+)", key)
            ]

        def coverage_stat(covdata: CoverageContainer | FileCoverage) -> CoverageStat:
            if by_metric == "branch":
                return covdata.branch_coverage()
            if by_metric == "decision":
                return covdata.decision_coverage().to_coverage_stat
            return covdata.line_coverage()

        def key_num_uncovered(covdata: CoverageContainer | FileCoverage) -> int:
            stat = coverage_stat(covdata)
            uncovered = stat.total - stat.covered
            return uncovered

        def key_percent_uncovered(covdata: CoverageContainer | FileCoverage) -> float:
            stat = coverage_stat(covdata)
            covered = stat.covered
            total = stat.total

            # No branches are always put directly after (or before when reversed)
            # files with 100% coverage (by assigning such files 110% coverage)
            return covered / total if total > 0 else 1.1

        if sort_key == "uncovered-number":
            # First sort filename alphabetical and then by the requested key
            return sorted(
                sorted(covdata_list, key=key_filename),
                key=key_num_uncovered,
                reverse=sort_reverse,
            )
        if sort_key == "uncovered-percent":
            # First sort filename alphabetical and then by the requested key
            return sorted(
                sorted(covdata_list, key=key_filename),
                key=key_percent_uncovered,
                reverse=sort_reverse,
            )

        # By default, we sort by filename alphabetically
        return sorted(covdata_list, key=key_filename, reverse=sort_reverse)

    def sorted_filecov(
        self,
        sort_key: Literal["filename", "uncovered-number", "uncovered-percent"],
        sort_reverse: bool,
        by_metric: Literal["line", "branch", "decision"],
        filename_uses_relative_pathname: bool = False,
        recurse: bool = False,
    ) -> list[FileCoverage]:
        """Sort a coverage dict.

        sort_key ("filename", "uncovered-number", "uncovered-percent"): the values to sort by
        sort_reverse (bool): reverse order if True
        by_metric ("line", "branch", "decision"): select the metric to sort
        filename_uses_relative_pathname (bool): for html, we break down a pathname to the
            relative path, but not for other formats.
        recurse (bool): whether to include file coverage from subdirectories

        returns: the sorted keys
        """

        return self.__sorted(
            list(self.filecov(recurse=recurse)),
            sort_key,
            sort_reverse,
            by_metric,
            filename_uses_relative_pathname,
        )

    def sorted_coverage(
        self,
        sort_key: Literal["filename", "uncovered-number", "uncovered-percent"],
        sort_reverse: bool,
        by_metric: Literal["line", "branch", "decision"],
        filename_uses_relative_pathname: bool = False,
    ) -> list[CoverageContainer | FileCoverage]:
        """Sort a coverage dict.

        sort_key ("filename", "uncovered-number", "uncovered-percent"): the values to sort by
        sort_reverse (bool): reverse order if True
        by_metric ("line", "branch", "decision"): select the metric to sort
        filename_uses_relative_pathname (bool): for html, we break down a pathname to the
            relative path, but not for other formats.

        returns: the sorted keys
        """

        return self.__sorted(
            list(self.values()),
            sort_key,
            sort_reverse,
            by_metric,
            filename_uses_relative_pathname,
        )

    @property
    def filename(self) -> str:
        """Helpful function for when we use this DirectoryCoverage in a union with FileCoverage"""
        return self.dirname

    def merge_lines(self, options: Options) -> None:
        """Merge line coverage for same line number. Remove the function information on merged lines."""
        self._stats = None
        for value in self.values():
            if isinstance(value, FileCoverage):
                value.merge_lines(
                    is_file_excluded(
                        "trace",
                        value.filename,
                        options.trace_include_filter,
                        options.trace_exclude_filter,
                    )
                )
            else:
                value.merge_lines(options)

    def merge(self, other: CoverageContainer, options: MergeOptions) -> None:
        """
        Merge CoverageContainer information.

        Do not use 'other' objects afterwards!
        """
        self._stats = None
        other._stats = None  # pylint: disable=protected-access
        # Set parent of items before merging them
        for item in other.values():
            if isinstance(item, CoverageContainer):
                item.parent = self
        self.data.merge(other.data, options)

    def insert_file_coverage(
        self, filecov: FileCoverage, options: MergeOptions
    ) -> None:
        """Add a file coverage item."""
        self._stats = None
        dirname = os.path.dirname(filecov.filename) + os.path.sep
        if dirname == self.dirname:
            key = filecov.filename
            if key in self.data:
                value = self.data[key]
                if not isinstance(value, FileCoverage):
                    raise TypeError(
                        f"Expected a FileCoverage object for key {key}, but got {type(value)}."
                    )
                value.merge(filecov, options)
            else:
                self.data[key] = filecov
        else:
            covdata_dirname = (
                os.path.join(
                    self.dirname,
                    os.path.relpath(dirname, self.dirname).split(
                        os.path.sep, maxsplit=1
                    )[0],
                )
                + os.path.sep
            )
            if covdata_dirname in self.data:
                covdata = self[covdata_dirname]
            else:
                covdata = self[covdata_dirname] = CoverageContainer(
                    covdata_dirname,
                    self,
                )
            if not isinstance(covdata, CoverageContainer):
                raise TypeError(
                    f"Expected a CoverageContainer object for key {covdata_dirname}, but got {type(covdata)}."
                )
            covdata.insert_file_coverage(filecov, options)

    @property
    def properties(self) -> dict[str, Any]:
        """Get the user defined properties."""
        return self._properties

    @property
    def stats(self) -> SummarizedStats:
        """Create a coverage statistic from a coverage data object."""
        if self._stats is None:
            self._stats = SummarizedStats.new_empty()
            for value in self.filecov(recurse=True):
                self._stats += value.stats

        return self._stats

    def line_coverage(self) -> CoverageStat:
        """A simple wrapper function necessary for sort_filecov()."""
        return self.stats.line

    def branch_coverage(self) -> CoverageStat:
        """A simple wrapper function necessary for sort_filecov()."""
        return self.stats.branch

    def decision_coverage(self) -> DecisionCoverageStat:
        """A simple wrapper function necessary for sort_filecov()."""
        return self.stats.decision
