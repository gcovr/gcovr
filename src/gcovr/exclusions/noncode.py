# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.4+main, a parsing and reporting tool for gcov.
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
Heuristics for ignoring data on lines that don't look like actual code.
"""

import re
import logging

from ..data_model.coverage import FileCoverage


LOGGER = logging.getLogger("gcovr")

_C_STYLE_COMMENT_PATTERN = re.compile(r"/\*.*?\*/")
_CPP_STYLE_COMMENT_PATTERN = re.compile(r"//.*?$")


def remove_unreachable_branches(filecov: FileCoverage, *, lines: list[str]) -> None:
    """Remove branches on lines that look like they don't contain useful code."""
    for linecov in filecov.linecov():
        if not linecov.has_reportable_branches:
            continue

        if _line_can_contain_branches(lines[linecov.lineno - 1]):
            continue

        LOGGER.debug(
            "%s Removing unreachable branch detected as compiler-generated code",
            linecov.location,
        )

        linecov.clear_branches()


def _line_can_contain_branches(code: str) -> bool:
    """
    False if the line looks empty except for braces.

    >>> _line_can_contain_branches('} // end something')
    False
    >>> _line_can_contain_branches('foo();')
    True
    """

    code = _CPP_STYLE_COMMENT_PATTERN.sub("", code)
    code = _C_STYLE_COMMENT_PATTERN.sub("", code)
    code = code.strip().replace(" ", "")
    return code not in ["", "{", "}", "{}"]


def remove_noncode_lines(filecov: FileCoverage, *, lines: list[str]) -> None:
    """Remove lines that look like non-code."""
    # iterate over a shallow copy
    for linecov in list(filecov.linecov()):
        source_code = lines[linecov.lineno - 1]
        if linecov.count == 0 and _is_non_code(source_code):
            LOGGER.debug(
                "%s Removing line detected as non code",
                linecov.location,
            )
            filecov.remove_line_coverage(linecov)


def _is_non_code(code: str) -> bool:
    """
    Check for patterns that indicate that this line doesn't contain useful code.

    Examples:
    >>> _is_non_code('  // some comment!')
    True
    >>> _is_non_code('  /* some comment! */')
    True
    >>> _is_non_code('} else {')  # could be easily made detectable
    False
    >>> _is_non_code('}else{')
    False
    >>> _is_non_code('else')
    True
    >>> _is_non_code('{')
    True
    >>> _is_non_code('/* some comment */ {')
    True
    >>> _is_non_code('}')
    True
    >>> _is_non_code('} // some code')
    True
    >>> _is_non_code('return {};')
    False
    """

    code = _CPP_STYLE_COMMENT_PATTERN.sub("", code)
    code = _C_STYLE_COMMENT_PATTERN.sub("", code)
    code = code.strip()
    return len(code) == 0 or code in ["{", "}", "else"]
