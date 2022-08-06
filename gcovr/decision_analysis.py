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

import logging
import re
from typing import (
    List,
    Tuple,
)

from .coverage import (
    DecisionCoverageUncheckable,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
    FileCoverage,
)

logger = logging.getLogger("gcovr")

_C_STYLE_COMMENT_PATTERN = re.compile(r"/\*.*?\*/")
_CPP_STYLE_COMMENT_PATTERN = re.compile(r"//.*?$")


# helper functions


def _prep_decision_string(code: str) -> str:
    r"""Prepare the input to analyze, if it's a branch statement.
    Remove comments, remove whitespace, add leading space to seperate branch-keywords
    from possible collisions with variable names.

    >>> _prep_decision_string('a++; if (a > 5) { // check for something ')
    ' a++; if (a > 5) {'
    """

    code = _CPP_STYLE_COMMENT_PATTERN.sub("", code)
    code = _C_STYLE_COMMENT_PATTERN.sub("", code)

    return " " + code.strip()


def _is_a_branch_statement(code: str) -> bool:
    r"""Checks, if the given line of code is a branch statement"""
    return any(
        s in _prep_decision_string(code)
        for s in (
            " if(",
            ";if(",
            " if (",
            ";if (",
            " case ",
            ";case ",
            " default:",
            ";default:",
        )
    )


def _is_a_oneline_branch(code: str) -> bool:
    r"""Checks, if the given line of code is a branch and branch statement and code block is in one line

    >>> _is_a_oneline_branch('if(a>5){a = 0;}')
    True
    """
    return re.match(r"^[^;]+{(?:.*;)*.*}$", _prep_decision_string(code)) is not None


def _is_a_loop(code: str) -> bool:
    r"""Checks, if the given line of code is a loop-statement (while,do-while,if)

    >>> _is_a_loop('while(5 < a) {')
    True
    """
    compare_string = _prep_decision_string(code)
    return any(
        s in compare_string
        for s in (" while(", " while (", "}while(", " for ", " for(")
    )


def _is_a_switch(code: str) -> bool:
    r"""Check if the given line relates to a switch-case label (case,default)

    >>> _is_a_switch('case 5:')
    True
    """
    compare_string = _prep_decision_string(code)
    return any(s in compare_string for s in (" case ", " default:"))


class DecisionParser:
    r"""Parses the decisions of a source file.

    Args:
        covdata:
            Reference to the active coverage data.
        lines:
            The encoding of the source files
    """

    def __init__(self, coverage: FileCoverage, lines: List[Tuple[int, str]]):
        self.coverage: FileCoverage = coverage
        self.lines: List[Tuple[int, str]] = lines

        # status variables for decision analysis
        self.decision_analysis_active: bool = (
            False  # set to True, once we're in the process of analyzing a branch
        )
        self.last_decision_line: int = 0
        self.decision_analysis_open_brackets: int = 0

    def parse_all_lines(self):
        logger.debug("Starting the decision analysis")

        # start to iterate through the lines
        for lineno, code in self.lines:
            self.parse_one_line(lineno, code)

        logger.debug("Decision Analysis finished!")

    def parse_one_line(self, lineno: int, code: str) -> None:
        line_coverage = self.coverage.lines.get(lineno)

        if line_coverage is None or line_coverage.noncode:
            return

        # check, if a analysis for a classic if-/else if-branch is active
        if self.decision_analysis_active:
            self.continue_multiline_decision_analysis(lineno, code)

        # if no decision analysis is active, check the active line of code for a branch_statement or a loop
        if self.decision_analysis_active:
            return
        if not (_is_a_branch_statement(code) or _is_a_loop(code)):
            return

        # check if a branch exists (prevent misdetection caused by inaccurante parsing)
        if len(line_coverage.branches.items()) > 0:
            if _is_a_loop(code) or _is_a_oneline_branch(code):
                if len(line_coverage.branches.items()) == 2:
                    keys = sorted(line_coverage.branches)
                    # if it's a compact decision, we can only use the fallback to analyze
                    # simple decisions via branch calls
                    line_coverage.decision = DecisionCoverageConditional(
                        line_coverage.branches[keys[0]].count,
                        line_coverage.branches[keys[1]].count,
                    )
                else:
                    # it's a compplex decision with more than 2 branches. No accurate detection possible
                    # Set the decision to uncheckable
                    line_coverage.decision = DecisionCoverageUncheckable()
                    logger.debug(f"Uncheckable decision at line {lineno}")
            else:
                self.start_multiline_decision_analysis(lineno, code)
                return

        # check if it's a case statement (measured at every line of a case, so a branch definition isn't given)
        elif _is_a_switch(code):
            if "; break;" in code.replace(" ", "").replace(";", "; "):
                # just use execution counts of case lines
                line_coverage.decision = DecisionCoverageSwitch(line_coverage.count)
            else:
                # use the execution counts of the following line (compatibility with GCC 5)
                line_coverage_next_line = self.coverage.lines.get(lineno + 1)
                if line_coverage_next_line is not None:
                    line_coverage.decision = DecisionCoverageSwitch(
                        line_coverage_next_line.count
                    )

    def start_multiline_decision_analysis(self, lineno: int, code: str) -> None:
        # normal (non-compact) branch, analyze execution of following lines
        self.decision_analysis_active = True
        self.last_decision_line = lineno

        # count brackets to make sure we're outside of the decision expression
        prepped_code = (
            "(" + _prep_decision_string(code).split(" if(")[-1].split(" if (")[-1]
        )
        self.decision_analysis_open_brackets += prepped_code.count("(")
        self.decision_analysis_open_brackets -= prepped_code.count(")")

    def continue_multiline_decision_analysis(self, lineno: int, code: str) -> None:
        line_coverage = self.coverage.lines.get(lineno)
        exec_count = 0 if line_coverage is None else line_coverage.count
        last_decision_line_cov = self.coverage.lines.get(self.last_decision_line)

        # check, if the branch statement was finished in the last line
        if self.decision_analysis_open_brackets == 0:
            # set execution counts for the decision. true is the exec_count.
            # false is the delta between executed blocks and executions of the decision statement.
            delta_count = last_decision_line_cov.count - exec_count
            if delta_count >= 0:
                last_decision_line_cov.decision = DecisionCoverageConditional(
                    exec_count,
                    delta_count,
                )
            else:
                last_decision_line_cov.decision = DecisionCoverageUncheckable()
                logger.debug(
                    f"Uncheckable decision at line {lineno}. (Delta = {delta_count})"
                )

            # disable the current decision analysis
            self.decision_analysis_active = False
            self.decision_analysis_open_brackets = 0
            return

        # count amount of open/closed brackets to track, when we can start checking if the block is executed
        prepped_code = _prep_decision_string(code)
        self.decision_analysis_open_brackets += prepped_code.count("(")
        self.decision_analysis_open_brackets -= prepped_code.count(")")
