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

import logging
import re

from .coverage import (
    DecisionCoverageUncheckable,
    DecisionCoverageConditional,
    DecisionCoverageSwitch,
)

logger = logging.getLogger("gcovr")

# for type annotations:
if False:
    from typing import (  # noqa, pylint: disable=all
        Callable,
        Dict,
        Iterable,
        List,
        Optional,
        Tuple,
    )

_C_STYLE_COMMENT_PATTERN = re.compile(r"/\*.*?\*/")
_CPP_STYLE_COMMENT_PATTERN = re.compile(r"//.*?$")


# helper functions


def prep_decision_string(code):
    r"""Prepare the input to analyze, if it's a branch statement.
    Remove comments, remove whitespace, add leading space to seperate branch-keywords
    from possible collisions with variable names.

    >>> prep_decision_string('a++; if (a > 5) { // check for something ')
    ' a++; if (a > 5) {'
    """

    code = _CPP_STYLE_COMMENT_PATTERN.sub("", code)
    code = _C_STYLE_COMMENT_PATTERN.sub("", code)

    return " " + code.strip()


def is_a_branch_statement(code):
    r"""Checks, if the given line of code is a branch statement"""
    return any(
        s in prep_decision_string(code)
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


def is_a_oneline_branch(code):
    r"""Checks, if the given line of code is a branch and branch statement and code block is in one line

    >>> is_a_oneline_branch('if(a>5){a = 0;}')
    True
    """
    return re.match(r"^[^;]+{(?:.*;)*.*}$", prep_decision_string(code)) is not None


def is_a_loop(code):
    r"""Checks, if the given line of code is a loop-statement (while,do-while,if)

    >>> is_a_loop('while(5 < a) {')
    True
    """
    compare_string = prep_decision_string(code)
    if any(
        s in compare_string
        for s in (" while(", " while (", "}while(", " for ", " for(")
    ):
        return True


def get_branch_type(code):
    r"""Returns the type of the branch statement used in the given line of code

    >>> get_branch_type('case 5:')
    'switch'
    """
    compare_string = prep_decision_string(code)
    if any(s in compare_string for s in (" if(", " if (")):
        return "if"
    elif any(s in compare_string for s in (" case ", " default:")):
        return "switch"
    return ""


class DecisionParser(object):
    r"""Parses the decisions of a source file.

    Args:
        fname:
            File name of the active source file.
        covdata:
            Reference to the active coverage data.
        lines:
            The encoding of the source files
    """

    def __init__(self, fname, coverage, lines):
        self.fname = fname
        self.coverage = coverage
        self.lines = lines

        # status variables for decision analysis
        self.decision_analysis_active = (
            False  # set to True, once we're in the process of analyzing a branch
        )
        self.last_decision_line = 0
        self.last_decision_line_exec_count = 0
        self.last_decision_type = "if"  # can be: "if" or "switch"
        self.decision_analysis_open_brackets = 0

    def parse_all_lines(self):
        logger.debug("Starting the decision analysis")

        # start to iterate through the lines
        for lineno, code in self.lines:
            exec_count = self.coverage.line(lineno).count

            if not self.coverage.line(lineno).noncode:
                line_coverage = self.coverage.line(lineno)
                # check, if a analysis for a classic if-/else if-branch is active
                if self.decision_analysis_active:
                    # check, if the branch statement was finished in the last line
                    if self.decision_analysis_open_brackets == 0:
                        # set execution counts for the decision. true is the exec_count.
                        # false is the delta between executed blocks and executions of the decision statement.
                        self.coverage.line(
                            self.last_decision_line
                        ).decision = DecisionCoverageConditional(
                            exec_count, self.last_decision_line_exec_count - exec_count
                        )

                        # disable the current decision analysis
                        self.decision_analysis_active = False
                        self.decision_analysis_open_brackets = 0

                    else:
                        # count amount of open/closed brackets to track, when we can start checking if the block is executed
                        self.decision_analysis_open_brackets += prep_decision_string(
                            code
                        ).count("(")
                        self.decision_analysis_open_brackets -= prep_decision_string(
                            code
                        ).count(")")

                # if no decision analysis is active, check the active line of code for a branch_statement or a loop
                if not self.decision_analysis_active and (
                    is_a_branch_statement(code) or is_a_loop(code)
                ):
                    # check if a branch exists (prevent misdetection caused by inaccurante parsing)
                    if len(line_coverage.branches.items()) > 0:
                        if is_a_loop(code) or is_a_oneline_branch(code):
                            if len(line_coverage.branches.items()) == 2:
                                # if it's a compact decision, we can only use the fallback to analyze
                                # simple decisions via branch calls
                                line_coverage.decision = DecisionCoverageConditional(
                                    line_coverage.branch(0).count,
                                    line_coverage.branch(1).count,
                                )
                            else:
                                # it's a compplex decision with more than 2 branches. No accurate detection possible
                                # Set the decision to uncheckable
                                line_coverage.decision = DecisionCoverageUncheckable()
                                logger.debug(f"Uncheckable decision at line {lineno}")
                        else:
                            # normal (non-compact) branch, analyze execution of following lines
                            self.decision_analysis_active = True
                            self.last_decision_line = lineno
                            self.last_decision_line_exec_count = line_coverage.count
                            self.last_decision_type = get_branch_type(code)
                            # count brackets to make sure we're outside of the decision expression
                            self.decision_analysis_open_brackets += (
                                "("
                                + prep_decision_string(code)
                                .split(" if(")[-1]
                                .split(" if (")[-1]
                            ).count("(")
                            self.decision_analysis_open_brackets -= (
                                "("
                                + prep_decision_string(code)
                                .split(" if(")[-1]
                                .split(" if (")[-1]
                            ).count(")")

                    # check if it's a case statement (measured at every line of a case, so a branch definition isn't given)
                    elif get_branch_type(code) == "switch":
                        if "; break;" in code.replace(" ", "").replace(";", "; "):
                            # just use execution counts of case lines
                            line_coverage.decision = DecisionCoverageSwitch(
                                line_coverage.count
                            )
                        else:
                            # use the execution counts of the following line (compatibility with GCC 5)
                            line_coverage.decision = DecisionCoverageSwitch(
                                self.coverage.line(lineno + 1).count
                            )

        logger.debug("Decision Analysis finished!")
