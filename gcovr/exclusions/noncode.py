# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.2
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2024 the gcovr authors
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

from typing import List
import re
import logging

from ..coverage import FileCoverage


LOGGER = logging.getLogger("gcovr")

_C_STYLE_COMMENT_PATTERN = re.compile(r"/\*.*?\*/")
_CPP_STYLE_COMMENT_PATTERN = re.compile(r"//.*?$")


def remove_unreachable_branches(filecov: FileCoverage, *, lines: List[str]) -> None:
    """Remove branches on lines that look like they don't contain useful code."""
    for linecov in filecov.lines.values():
        if not linecov.branches:
            continue

        if _line_can_contain_branches(lines[linecov.lineno - 1]):
            continue

        LOGGER.debug(
            "Excluding unreachable branch on line %d file %s: detected as compiler-generated code",
            linecov.lineno,
            filecov.filename,
        )

        linecov.branches = {}


def remove_noncode_lines(filecov: FileCoverage, *, lines: List[str]) -> None:
    """Remove lines that look like non-code."""
    # iterate over a shallow copy
    for linecov in list(filecov.lines.values()):
        source_code = lines[linecov.lineno - 1]
        if linecov.count == 0 and _is_non_code(source_code):
            filecov.lines.pop(linecov.lineno)


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
