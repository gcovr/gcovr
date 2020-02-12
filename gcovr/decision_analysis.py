# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2020 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import re
import io

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
        source_encoding:
            The encoding of the source files
        logger:
            The logger to which decision analysis logs should be written to.
    """

    def __init__(self, fname, coverage, source_encoding, logger):
        self.fname = fname
        self.coverage = coverage
        self.source_encoding = source_encoding
        self.logger = logger

        # status variables for decision analysis
        self.decision_analysis_active = (
            False  # set to True, once we're in the process of analyzing a branch
        )
        self.last_decision_line = 0
        self.last_decision_line_exec_count = 0
        self.last_decision_type = "if"  # can be: "if" or "switch"
        self.decision_analysis_open_brackets = 0

    def parse_all_lines(self):
        self.logger.verbose_msg("Starting the decision analysis")

        # load all the lines of the source file
        with io.open(
            self.fname, "r", encoding=self.source_encoding, errors="replace"
        ) as INPUT:
            self.source_lines = [line.rstrip() for line in INPUT.read().splitlines()]

        # start to iterate through the lines
        for lineno, code in enumerate(self.source_lines, 1):
            exec_count = self.coverage.line(lineno).count

            if not self.coverage.line(lineno).noncode:
                line_coverage = self.coverage.line(lineno)
                # check, if a analysis for a classic if-/else if-branch is active
                if self.decision_analysis_active:
                    # check, if the branch statement was finished in the last line
                    if self.decision_analysis_open_brackets == 0:
                        # set execution counts for the decision. true is the exec_count.
                        # false is the delta between executed blocks and executions of the decision statement.
                        self.coverage.line(self.last_decision_line).decision(
                            0
                        ).count = exec_count
                        self.coverage.line(self.last_decision_line).decision(
                            1
                        ).count = (self.last_decision_line_exec_count - exec_count)

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
                                line_coverage.decision(0).update_count(
                                    line_coverage.branch(0).count
                                )
                                line_coverage.decision(1).update_count(
                                    line_coverage.branch(1).count
                                )
                            else:
                                # it's a compplex decision with more than 2 branches. No accurate detection possible
                                # Set the decision to uncheckable
                                line_coverage.decision(0).update_uncheckable(True)
                                line_coverage.decision(1).update_uncheckable(True)
                                self.logger.verbose_msg(
                                    "Uncheckable decision at line {line}", line=lineno
                                )
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
                            line_coverage.decision(0).count = line_coverage.count
                        else:
                            # use the execution counts of the following line (compatibility with GCC 5)
                            line_coverage.decision(0).count = self.coverage.line(
                                lineno + 1
                            ).count

        self.logger.verbose_msg("Decision Analysis finished!")
