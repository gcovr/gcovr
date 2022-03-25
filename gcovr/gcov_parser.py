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
Handle parsing of the textual ``.gcov`` file format.

Other modules should only use the following items:
`parse_metadata()`, `parse_coverage()`, `ParserFlags`, `UnknownLineType`.

The behavior of this parser was informed by the following sources:

* the old GcovParser class
  <https://github.com/gcovr/gcovr/blob/e0b7afef00123b7b6ce4f487a1c4cc9fc60528bc/gcovr/gcov.py#L239>
* the *Invoking Gcov* section in the GCC manual (version 11)
  <https://gcc.gnu.org/onlinedocs/gcc-11.1.0/gcc/Invoking-Gcov.html>
* the ``gcov.c`` source code in GCC
  (especially for understanding the exact number format)
  <https://github.com/gcc-mirror/gcc/blob/releases/gcc-11.1.0/gcc/gcov.c>
"""
# pylint: disable=too-many-lines


import enum
import logging
import re

from typing import (
    List,
    Dict,
    NamedTuple,
    Optional,
    Union,
    Tuple,
    Callable,
    Pattern,
    NoReturn,
)

from .coverage import FileCoverage
from .decision_analysis import DecisionParser

logger = logging.getLogger("gcovr")

_EXCLUDE_LINE_FLAG = "_EXCL_"
_EXCLUDE_LINE_PATTERN_POSTFIX = r"_EXCL_(LINE|START|STOP)"

_C_STYLE_COMMENT_PATTERN = re.compile(r"/\*.*?\*/")
_CPP_STYLE_COMMENT_PATTERN = re.compile(r"//.*?$")


def _line_pattern(pattern: str) -> Pattern[str]:
    """
    Compile a regex from a line pattern.

    A line pattern is a normal regex, except that the following placeholders
    will be replaced by pattern fragments:

    * ``VALUE`` -> matches gcov's ``format_gcov()`` output (percentage or
      human-readable)
    * ``INT`` -> matches an integer
    * the pattern is anchored at the start/end
    * space is replaced by ``[ ]+``
    """
    pattern = pattern.replace(" ", r"[ ]+")
    pattern = pattern.replace("INT", r"[0-9]+")
    pattern = pattern.replace("VALUE", r"[0-9.]+[%kMGTPEZY]?")
    return re.compile("^" + pattern + "$")


_RE_FUNCTION_LINE = _line_pattern(
    r"function (.*?) called (INT) returned (VALUE) blocks executed (VALUE)"
)
_RE_BRANCH_LINE = _line_pattern(
    r"branch (INT) (?:taken (VALUE)(?: \((\w+)\))?|never executed)"
)
_RE_CALL_LINE = _line_pattern(r"call (INT) (?:returned (VALUE)|never executed)")
_RE_UNCONDITIONAL_LINE = _line_pattern(
    r"unconditional (INT) (?:taken (VALUE)|never executed)"
)
_RE_SOURCE_LINE = _line_pattern(r"(?: )?(VALUE[*]?|-|[#]{5}|[=]{5}):(?: )?(INT):(.*)")
_RE_BLOCK_LINE = _line_pattern(r"(?: )?(VALUE|[$]{5}|[%]{5}): (INT)-block (INT)")


class _ExtraInfo(enum.Flag):
    """Additional info about lines, such as noncode or exception-only status."""

    NONE = 0
    NONCODE = enum.auto()
    EXCEPTION_ONLY = enum.auto()
    PARTIAL = enum.auto()

    def __repr__(self) -> str:
        return str(self).replace("_ExtraInfo.", "")


class _SourceLine(NamedTuple):
    """A gcov line with source code: ``HITS: LINENO:CODE``"""

    hits: int
    lineno: int
    source_code: str
    extra_info: _ExtraInfo


class _MetadataLine(NamedTuple):
    """A gcov line with metadata: ``-: 0:KEY:VALUE``"""

    key: str
    value: str


class _BlockLine(NamedTuple):
    """A gcov line with block data: ``HITS: LINENO-block BLOCKNO``"""

    hits: int
    lineno: int
    blockno: int
    extra_info: _ExtraInfo


class _SpecializationMarkerLine(NamedTuple):
    """A gcov line that delimits template specialization sections (no fields)"""


class _SpecializationNameLine(NamedTuple):
    """A gcov line with the name of a specialization section: ``NAME:``"""

    name: str


class _CallLine(NamedTuple):
    """A gcov line with call data: ``call CALLNO returned RETURNED``"""

    callno: int
    returned: int


class _BranchLine(NamedTuple):
    """A gcov line with branch data: ``branch BRANCHNO taken HITS (ANNOTATION)``"""

    branchno: int
    hits: int
    annotation: Optional[str]


class _UnconditionalLine(NamedTuple):
    """
    A gcov line with unconditional branch data: ``unconditional BRANCHNO taken HITS``
    """

    branchno: int
    hits: int


class _FunctionLine(NamedTuple):
    """
    A gcov line with function coverage data for the next line.

    ``function NAME called CALLS returned RETURNED blocks executed BLOCKS``
    """

    name: str
    calls: int
    returned: int
    blocks_covered: int


# NamedTuples can't inherit from a common base,
# so we use a Union type as the parse_line() return type.
#
# Why NamedTuples? Better type safety than tuples, but very low memory overhead.
_Line = Union[
    _SourceLine,
    _MetadataLine,
    _BlockLine,
    _SpecializationMarkerLine,
    _SpecializationNameLine,
    _CallLine,
    _BranchLine,
    _UnconditionalLine,
    _FunctionLine,
]


class UnknownLineType(Exception):
    """Used by `parse_line()` to signal that no known line type matched."""

    def __init__(self, line: str) -> None:
        super().__init__(line)
        self.line = line


def parse_metadata(lines: List[str]) -> Dict[str, str]:
    r"""
    Collect the header/metadata lines from a gcov file.

    Example:
    >>> parse_metadata('''
    ...   -: 0:Foo:bar
    ...   -: 0:Key:123
    ... '''.splitlines())
    {'Foo': 'bar', 'Key': '123'}
    """
    collected = {}
    for line in lines:

        # empty lines shouldn't occur in reality, but are common in testing
        if not line:
            continue

        parsed_line = _parse_line(line)

        if isinstance(parsed_line, _MetadataLine):
            key, value = parsed_line
            collected[key] = value
        else:
            break  # stop at the first line that is not metadata

    return collected


class ParserFlags(enum.Flag):
    """
    Flags/toggles that control `parse_coverage()`.

    Multiple values can be combined with binary-or::

        ParserFlags.IGNORE_PASS_ERRORS | ParserFlags.EXCLUDE_THROW_BRANCHES
    """

    NONE = 0
    """Default behavior."""

    IGNORE_PARSE_ERRORS = enum.auto()
    """Whether parse errors shall be converted to warnings."""

    EXCLUDE_FUNCTION_LINES = enum.auto()
    """Whether coverage shall be ignored on lines that introduce a function."""

    EXCLUDE_INTERNAL_FUNCTIONS = enum.auto()
    """Whether function coverage for reserved names is ignored."""

    EXCLUDE_UNREACHABLE_BRANCHES = enum.auto()
    """Whether branch coverage shall be ignored on lines without useful code."""

    EXCLUDE_THROW_BRANCHES = enum.auto()
    """Whether coverage for exception-only branches shall be ignored."""

    RESPECT_EXCLUSION_MARKERS = enum.auto()
    """Whether the eclusion markers shall be used."""

    PARSE_DECISIONS = enum.auto()
    """Whether decision coverage shall be generated."""


_LineWithError = Tuple[str, Exception]


class _Context(NamedTuple):
    flags: ParserFlags
    filename: str


def parse_coverage(
    lines: List[str],
    *,
    filename: str,
    exclude_lines_by_pattern: Optional[str],
    exclude_pattern_prefix: Optional[str],
    flags: ParserFlags,
) -> FileCoverage:
    """
    Extract coverage data from a gcov report.

    Logging:
    Parse problems are reported as warnings.
    Coverage exclusion decisions are reported as verbose messages.

    Arguments:
        lines: the lines of the file to be parsed (excluding newlines)
        filename: for error reports
        exclude_lines_by_pattern: string with regex syntax to exclude
            individual lines
        exclude_pattern_prefix: string with prefix for _LINE/_START/_STOP markers.
        flags: various choices for the parser behavior

    Returns:
        the coverage data

    Raises:
        Any exceptions during parsing, unless `ParserFlags.IGNORE_PARSE_ERRORS`
        is enabled.
    """

    context = _Context(flags, filename)

    lines_with_errors: List[_LineWithError] = []

    tokenized_lines: List[Tuple[_Line, str]] = []
    for raw_line in lines:

        # empty lines shouldn't occur in reality, but are common in testing
        if not raw_line:
            continue

        try:
            tokenized_lines.append((_parse_line(raw_line), raw_line))
        except Exception as ex:  # pylint: disable=broad-except
            lines_with_errors.append((raw_line, ex))

    if (
        flags & ParserFlags.RESPECT_EXCLUSION_MARKERS
        or flags & ParserFlags.PARSE_DECISIONS
    ):
        src_lines = [
            (line.lineno, line.source_code)
            for line, _ in tokenized_lines
            if isinstance(line, _SourceLine)
        ]

    if flags & ParserFlags.RESPECT_EXCLUSION_MARKERS:
        line_is_excluded = _find_excluded_ranges(
            lines=src_lines,
            warnings=_ExclusionRangeWarnings(filename),
            exclude_lines_by_pattern=exclude_lines_by_pattern,
            exclude_pattern_prefix=exclude_pattern_prefix,
        )
    else:
        line_is_excluded = _make_is_in_any_range([])

    coverage = FileCoverage(filename)
    state = _ParserState()
    for line, raw_line in tokenized_lines:
        try:
            state = _gather_coverage_from_line(
                state,
                line,
                coverage=coverage,
                line_is_excluded=line_is_excluded,
                context=context,
            )
        except Exception as ex:  # pylint: disable=broad-except
            lines_with_errors.append((raw_line, ex))
            state = _ParserState(is_recovering=True)

    # Clean up the final state. This shouldn't happen,
    # but the last line could theoretically contain pending function lines
    for function in state.deferred_functions:
        _add_coverage_for_function(coverage, state.lineno + 1, function, context)

    if flags & ParserFlags.PARSE_DECISIONS:
        decision_parser = DecisionParser(filename, coverage, src_lines)
        decision_parser.parse_all_lines()

    _report_lines_with_errors(lines_with_errors, context)

    return coverage


class _ParserState(NamedTuple):
    deferred_functions: List[_FunctionLine] = []
    lineno: int = 0
    is_excluded: bool = False
    line_contents: str = ""
    is_recovering: bool = False


def _gather_coverage_from_line(
    state: _ParserState,
    line: _Line,
    *,
    coverage: FileCoverage,
    line_is_excluded: Callable[[int], bool],
    context: _Context,
) -> _ParserState:
    """
    Interpret a Line, updating the FileCoverage, and transitioning ParserState.

    The function handles all possible Line variants, and dies otherwise:
    >>> _gather_coverage_from_line(_ParserState(), "illegal line type",
    ...     coverage=..., line_is_excluded=..., context=...)
    Traceback (most recent call last):
    AssertionError: Unexpected variant: 'illegal line type'
    """
    # pylint: disable=too-many-return-statements,too-many-branches
    # pylint: disable=no-else-return  # make life easier for type checkers

    if isinstance(line, _SourceLine):
        lineno = line.lineno
        is_excluded = line_is_excluded(lineno)
        noncode, count = _line_noncode_and_count(
            line,
            flags=context.flags,
            is_excluded=is_excluded,
            is_function=bool(state.deferred_functions),
        )

        if noncode:
            coverage.line(lineno).noncode = True
        elif count is not None:
            coverage.line(lineno).count += count

        # handle deferred functions
        for function in state.deferred_functions:
            _add_coverage_for_function(coverage, line.lineno, function, context)

        return _ParserState(
            lineno=line.lineno,
            line_contents=line.source_code,
            is_excluded=is_excluded,
        )

    elif state.is_recovering:
        return state  # skip until the next _SourceLine

    elif isinstance(line, _FunctionLine):
        # Defer handling of the function tag until the next source line.
        # This is important to get correct line number information.
        return state._replace(deferred_functions=[*state.deferred_functions, line])

    elif isinstance(line, _BranchLine):
        branchno, count, annotation = line

        exclusion_reason = _branch_can_be_excluded(line, state, context.flags)
        if exclusion_reason:
            logger.debug(
                f"Excluding unreachable branch on line {state.lineno} in file {context.filename}: {exclusion_reason}"
            )
            return state

        branch_cov = coverage.line(state.lineno).branch(branchno)
        branch_cov.count += count
        if annotation == "fallthrough":
            branch_cov.fallthrough = True
        if annotation == "throw":
            branch_cov.throw = True

        return state

    # ignore metadata in this phase
    elif isinstance(line, _MetadataLine):
        return state

    # currently, the parser just ignores specialization sections
    elif isinstance(line, (_SpecializationMarkerLine, _SpecializationNameLine)):
        return state

    # ignore unused line types, such as specialization sections
    elif isinstance(line, (_CallLine, _UnconditionalLine, _BlockLine)):
        return state

    else:
        return _assert_never(line)


def _assert_never(never: NoReturn) -> NoReturn:
    """Used for the type checker"""
    raise AssertionError(f"Unexpected variant: {never!r}")


def _report_lines_with_errors(
    lines_with_errors: List[_LineWithError], context: _Context
) -> None:
    """Log warnings and potentially re-throw exceptions"""

    if not lines_with_errors:
        return

    lines = [line for line, _ in lines_with_errors]
    errors = [error for _, error in lines_with_errors]

    lines_output = "\n\t  ".join(lines)
    logger.warning(
        f"Unrecognized GCOV output for {context.filename}\n"
        f"\t  {lines_output}\n"
        "\tThis is indicative of a gcov output parse error.\n"
        "\tPlease report this to the gcovr developers\n"
        "\tat <https://github.com/gcovr/gcovr/issues>."
    )

    for ex in errors:
        logger.warning(f"Exception during parsing:\n\t{type(ex).__name__}: {ex}")

    if context.flags & ParserFlags.IGNORE_PARSE_ERRORS:
        return

    logger.error(
        "Exiting because of parse errors.\n"
        "\tYou can run gcovr with --gcov-ignore-parse-errors\n"
        "\tto continue anyway."
    )

    # if we caught an exception, re-raise it for the traceback
    raise errors[0]  # guaranteed to have at least one exception


def _line_noncode_and_count(
    line: _SourceLine, *, flags: ParserFlags, is_excluded: bool, is_function: bool
) -> Tuple[bool, Optional[int]]:
    """
    Some reports like JSON are sensitive to which lines are excluded,
    so keep this convoluted logic for now.

    The count field is only meaningful if not(noncode).
    """

    raw_count, _, source_code, extra_info = line

    if flags & ParserFlags.EXCLUDE_FUNCTION_LINES and is_function:
        return True, None

    if is_excluded:
        return True, None

    if extra_info & _ExtraInfo.NONCODE:
        if _is_non_code(source_code):
            return True, None
        return False, None  # completely ignore this line

    if raw_count == 0 and _is_non_code(source_code):
        return True, None

    return False, raw_count


def _function_can_be_excluded(name: str, flags: ParserFlags) -> bool:
    # special names for construction/destruction of static objects will be ignored
    if flags & ParserFlags.EXCLUDE_INTERNAL_FUNCTIONS:
        if name.startswith("__") or name.startswith("_GLOBAL__sub_I_"):
            return True

    return False


def _branch_can_be_excluded(
    branch: _BranchLine, state: _ParserState, flags: ParserFlags
) -> Optional[str]:
    if state.is_excluded:
        return "marked with exclude pattern"

    if flags & ParserFlags.EXCLUDE_UNREACHABLE_BRANCHES:
        if not _line_can_contain_branches(state.line_contents):
            return "detected as compiler-generated code"

    if flags & ParserFlags.EXCLUDE_THROW_BRANCHES:
        if branch.annotation == "throw":
            return "detected as exception-only code"

    return None


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


def _add_coverage_for_function(
    coverage: FileCoverage,
    lineno: int,
    function: _FunctionLine,
    context: _Context,
) -> None:
    name, calls, _, _ = function

    if _function_can_be_excluded(name, context.flags):
        logger.debug(
            f"Ignoring Symbol {name} in line {lineno} in file {context.filename}"
        )
        return

    function_cov = coverage.function(name)
    function_cov.lineno = lineno
    function_cov.count += calls


def _parse_line(line: str) -> _Line:
    """
    Categorize/parse individual lines without further processing.

    Example: can parse code line:
    >>> _parse_line('     -: 13:struct Foo{};')
    _SourceLine(hits=0, lineno=13, source_code='struct Foo{};', extra_info=NONCODE)
    >>> _parse_line('    12: 13:foo += 1;  ')
    _SourceLine(hits=12, lineno=13, source_code='foo += 1;  ', extra_info=NONE)
    >>> _parse_line(' #####: 13:foo += 1;')
    _SourceLine(hits=0, lineno=13, source_code='foo += 1;', extra_info=NONE)
    >>> _parse_line(' =====: 13:foo += 1;')
    _SourceLine(hits=0, lineno=13, source_code='foo += 1;', extra_info=EXCEPTION_ONLY)
    >>> _parse_line('   12*: 13:cond ? f() : g();')
    _SourceLine(hits=12, lineno=13, source_code='cond ? f() : g();', extra_info=PARTIAL)
    >>> _parse_line(' 1.7k*: 13:foo();')
    _SourceLine(hits=1700, lineno=13, source_code='foo();', extra_info=PARTIAL)

    Example: can parse metadata line:
    >>> _parse_line('  -: 0:Foo:bar baz')
    _MetadataLine(key='Foo', value='bar baz')
    >>> _parse_line('  -: 0:Some key:2')  # coerce numbers
    _MetadataLine(key='Some key', value='2')

    Example: can parse branch tags:
    >>> _parse_line('branch 3 taken 15%')
    _BranchLine(branchno=3, hits=1, annotation=None)
    >>> _parse_line('branch 3 taken 0%')
    _BranchLine(branchno=3, hits=0, annotation=None)
    >>> _parse_line('branch 3 taken 123')
    _BranchLine(branchno=3, hits=123, annotation=None)
    >>> _parse_line('branch 7 taken 3% (fallthrough)')
    _BranchLine(branchno=7, hits=1, annotation='fallthrough')
    >>> _parse_line('branch 17 taken 99% (throw)')
    _BranchLine(branchno=17, hits=1, annotation='throw')
    >>> _parse_line('branch  0 never executed')
    _BranchLine(branchno=0, hits=0, annotation=None)
    >>> _parse_line('branch 2 with some unknown format')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType: branch 2 with some unknown format

    Example: can parse call tags:
    >>> _parse_line('call  0 never executed')
    _CallLine(callno=0, returned=0)
    >>> _parse_line('call  17 returned 50%')
    _CallLine(callno=17, returned=1)
    >>> _parse_line('call  17 returned 9')
    _CallLine(callno=17, returned=9)
    >>> _parse_line('call 2 with some unknown format')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType: call 2 with some unknown format

    Example: can parse unconditional branches
    >>> _parse_line('unconditional 1 taken 17')
    _UnconditionalLine(branchno=1, hits=17)
    >>> _parse_line('unconditional with some unknown format')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType: unconditional with some unknown format

    Example: can parse function tags:
    >>> _parse_line('function foo called 2 returned 95% blocks executed 85%')
    _FunctionLine(name='foo', calls=2, returned=1, blocks_covered=1)
    >>> _parse_line('function foo with some unknown format')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType: function foo with some unknown format

    Example: can parse template specialization markers:
    >>> _parse_line('------------------')
    _SpecializationMarkerLine()

    Example: can parse template specialization names:
    >>> _parse_line('Foo<bar>::baz():')
    _SpecializationNameLine(name='Foo<bar>::baz()')
    >>> _parse_line(' foo:')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType:  foo:
    >>> _parse_line(':')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType: :


    Example: can parse block line:
    >>> _parse_line('     1: 32-block  0')
    _BlockLine(hits=1, lineno=32, blockno=0, extra_info=NONE)
    >>> _parse_line(' %%%%%: 33-block  1')
    _BlockLine(hits=0, lineno=33, blockno=1, extra_info=NONE)
    >>> _parse_line(' $$$$$: 33-block  1')
    _BlockLine(hits=0, lineno=33, blockno=1, extra_info=EXCEPTION_ONLY)
    >>> _parse_line('     1: 9-block with some unknown format')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType:      1: 9-block with some unknown format

    Example: will reject garbage:
    >>> _parse_line('nonexistent_tag foo bar')
    Traceback (most recent call last):
    gcovr.gcov_parser.UnknownLineType: nonexistent_tag foo bar
    """
    # pylint: disable=too-many-branches

    tag = _parse_tag_line(line)
    if tag is not None:
        return tag

    # Handle lines that are like source lines.
    # But this could also include metadata lines and block-coverage lines.

    # CODE
    #
    # Structure: "COUNT: LINENO:CODE"
    #
    # Examples:
    #     -: 13:struct Foo{};
    #    12: 13:foo += 1;
    # #####: 13:foo += 1;
    # =====: 13:foo += 1;
    #   12*: 13:cond ? bar() : baz();
    match = _RE_SOURCE_LINE.fullmatch(line)
    if match is not None:
        count_str, lineno, source_code = match.groups()

        # METADATA (key, value)
        if count_str == "-" and lineno == "0":
            key, value = source_code.split(":", 1)
            return _MetadataLine(key, value)

        if count_str == "-":
            count = 0
            extra_info = _ExtraInfo.NONCODE
        elif count_str == "#####":
            count = 0
            extra_info = _ExtraInfo.NONE
        elif count_str == "=====":
            count = 0
            extra_info = _ExtraInfo.EXCEPTION_ONLY
        elif count_str.endswith("*"):
            count = _int_from_gcov_unit(count_str[:-1])
            extra_info = _ExtraInfo.PARTIAL
        else:
            count = _int_from_gcov_unit(count_str)
            extra_info = _ExtraInfo.NONE

        return _SourceLine(count, int(lineno), source_code, extra_info)

    # BLOCK
    #
    # Structure: "COUNT: LINENO-block BLOCKNO"
    if "-block " in line:
        match = _RE_BLOCK_LINE.match(line)
        if match is not None:
            count_str, lineno, blockno = match.groups()

            if count_str == "%%%%%":
                count = 0
                extra_info = _ExtraInfo.NONE
            elif count_str == "$$$$$":
                count = 0
                extra_info = _ExtraInfo.EXCEPTION_ONLY
            else:
                count = _int_from_gcov_unit(count_str)
                extra_info = _ExtraInfo.NONE

            return _BlockLine(count, int(lineno), int(blockno), extra_info)

    # SPECIALIZATION NAME
    #
    # Structure: a name starting in the first column, ending with a ":". It is
    # not safe to make further assumptions about the layout of the (demangled)
    # identifier. For example, Rust might produce "<X as Y>::foo::h12345".
    #
    # This line type is therefore checked LAST! The old parser might have been
    # more robust because it would only consider specialization names on the
    # line following a specialization marker.
    if len(line) > 2 and not line[0].isspace() and line.endswith(":"):
        return _SpecializationNameLine(line[:-1])

    raise UnknownLineType(line)


def _parse_tag_line(line: str) -> Optional[_Line]:
    """A tag line is any gcov line that starts in the first column."""
    # pylint: disable=too-many-return-statements

    # Tag lines never start with whitespace.
    #
    # In principle, specialization names are also like tag lines.
    # But they don't have a marker, so their detection is done last.
    if line.startswith(" "):
        return None

    # BRANCH
    #
    # Structure:
    # branch BRANCHNO never executed
    # branch BRANCHNO taken VALUE
    # branch BRANCHNO taken VALUE (ANNOTATION)
    if line.startswith("branch "):
        match = _RE_BRANCH_LINE.match(line)
        if match is not None:
            branch_id, taken_str, annotation = match.groups()
            hits = 0 if taken_str is None else _int_from_gcov_unit(taken_str)
            return _BranchLine(int(branch_id), hits, annotation)

    # CALL
    #
    # Structure (note whitespace after tag):
    # call  0 never executed
    # call  1 returned VALUE
    if line.startswith("call "):
        match = _RE_CALL_LINE.match(line)
        if match is not None:
            call_id, returned_str = match.groups()
            returned = 0 if returned_str is None else _int_from_gcov_unit(returned_str)
            return _CallLine(int(call_id), returned)

    # UNCONDITIONAL
    #
    # Structure:
    # unconditional NUM taken VALUE
    # unconditional NUM never executed
    if line.startswith("unconditional "):
        match = _RE_UNCONDITIONAL_LINE.match(line)
        if match is not None:
            branch_id, taken_str = match.groups()
            taken = 0 if taken_str is None else _int_from_gcov_unit(taken_str)
            return _UnconditionalLine(int(branch_id), taken)

    # FUNCTION
    #
    # Structure:
    # function NAME called VALUE returned VALUE blocks executed VALUE
    if line.startswith("function "):
        match = _RE_FUNCTION_LINE.match(line)
        if match is not None:
            name, calls, returns, blocks = match.groups()
            return _FunctionLine(
                name,
                _int_from_gcov_unit(calls),
                _int_from_gcov_unit(returns),
                _int_from_gcov_unit(blocks),
            )

    # SPECIALIZATION MARKER
    #
    # Structure: literally just lots of hyphens
    if line.startswith("-----"):
        return _SpecializationMarkerLine()

    return None


class _ExclusionRangeWarnings:
    r"""
    Log warnings related to exclusion marker processing.

    Example:
    >>> source = '''\
    ...  1: 1: some code
    ...  1: 2: foo // LCOV_EXCL_STOP
    ...  1: 3: bar // GCOVR_EXCL_START
    ...  1: 4: bar // GCOVR_EXCL_LINE
    ...  1: 5: baz // GCOV_EXCL_STOP
    ...  1: 6: "GCOVR_EXCL_START"
    ... '''
    >>> caplog = getfixture('caplog')
    >>> caplog.clear()
    >>> _ = parse_coverage(  # doctest: +NORMALIZE_WHITESPACE
    ...     source.splitlines(), filename='example.cpp',
    ...     flags=ParserFlags.RESPECT_EXCLUSION_MARKERS, exclude_lines_by_pattern=None,
    ...     exclude_pattern_prefix='[GL]COVR?')
    >>> for message in caplog.record_tuples:
    ...     print(f"{message[1]}: {message[2]}")
    30: mismatched coverage exclusion flags.
              LCOV_EXCL_STOP found on line 2 without corresponding LCOV_EXCL_START, when processing example.cpp.
    30: GCOVR_EXCL_LINE found on line 4 in excluded region started on line 3, when processing example.cpp.
    30: GCOVR_EXCL_START found on line 3 was terminated by GCOV_EXCL_STOP on line 5, when processing example.cpp.
    30: The coverage exclusion region start flag GCOVR_EXCL_START
              on line 6 did not have corresponding GCOVR_EXCL_STOP flag
              in file example.cpp.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def mismatched_start_stop(
        self, start_lineno: int, start: str, stop_lineno: int, stop: str
    ) -> None:
        """warn that start/stop region markers don't match"""
        logger.warning(
            f"{start} found on line {start_lineno} "
            f"was terminated by {stop} on line {stop_lineno}, "
            f"when processing {self.filename}."
        )

    def stop_without_start(self, lineno: int, expected_start: str, stop: str) -> None:
        """warn that a region was ended without corresponding start marker"""
        logger.warning(
            "mismatched coverage exclusion flags.\n"
            f"          {stop} found on line {lineno} without corresponding {expected_start}, "
            f"when processing {self.filename}."
        )

    def start_without_stop(self, lineno: int, start: str, expected_stop: str) -> None:
        """warn that a region was started but not closed"""
        logger.warning(
            f"The coverage exclusion region start flag {start}\n"
            f"          on line {lineno} did not have corresponding {expected_stop} flag\n"
            f"          in file {self.filename}."
        )

    def line_after_start(self, lineno: int, start: str, start_lineno: str) -> None:
        """warn that a region was started but an excluded line was found"""
        logger.warning(
            f"{start} found on line {lineno} in excluded region started on line {start_lineno}, "
            f"when processing {self.filename}."
        )


def _find_excluded_ranges(
    lines: List[Tuple[int, str]],
    *,
    warnings: _ExclusionRangeWarnings,
    exclude_lines_by_pattern: Optional[str] = None,
    exclude_pattern_prefix: str,
) -> Callable[[int], bool]:
    """
    Scan through all lines to find line ranges covered by exclusion markers.

    Example:
    >>> lines = [(11, '//PREFIX_EXCL_LINE'), (13, '//IGNORE'), (15, '//PREFIX_EXCL_START'), (18, '//PREFIX_EXCL_STOP')]
    >>> exclude = _find_excluded_ranges(
    ...     lines, warnings=..., exclude_lines_by_pattern = '.*IGNORE', exclude_pattern_prefix='PREFIX')
    >>> [lineno for lineno in range(20) if exclude(lineno)]
    [11, 13, 15, 16, 17]
    """
    exclude_lines_by_pattern_regex = None
    if exclude_lines_by_pattern:
        exclude_lines_by_pattern_regex = re.compile(exclude_lines_by_pattern)

    # possibly overlapping half-open ranges of lines that are excluded
    exclude_line_ranges: List[Tuple[int, int]] = []

    exclusion_stack = []
    for lineno, code in lines:
        if _EXCLUDE_LINE_FLAG in code:
            # process the exclusion marker
            #
            # header is a marker name like LCOV or GCOVR
            #
            # START flags are added to the exlusion stack
            # STOP flags remove a marker from the exclusion stack
            excl_line_pattern = re.compile(
                "(" + exclude_pattern_prefix + ")" + _EXCLUDE_LINE_PATTERN_POSTFIX
            )
            for header, flag in excl_line_pattern.findall(code):

                if flag == "LINE":
                    if exclusion_stack:
                        warnings.line_after_start(
                            lineno, f"{header}_EXCL_LINE", exclusion_stack[-1][1]
                        )
                    else:
                        exclude_line_ranges.append((lineno, lineno + 1))

                if flag == "START":
                    exclusion_stack.append((header, lineno))

                elif flag == "STOP":
                    if not exclusion_stack:
                        warnings.stop_without_start(
                            lineno, f"{header}_EXCL_START", f"{header}_EXCL_STOP"
                        )
                        continue

                    start_header, start_lineno = exclusion_stack.pop()
                    if header != start_header:
                        warnings.mismatched_start_stop(
                            start_lineno,
                            f"{start_header}_EXCL_START",
                            lineno,
                            f"{header}_EXCL_STOP",
                        )

                    exclude_line_ranges.append((start_lineno, lineno))

                else:  # pragma: no cover
                    pass

        if exclude_lines_by_pattern_regex:
            if exclude_lines_by_pattern_regex.match(code):
                exclude_line_ranges.append((lineno, lineno + 1))

    for header, lineno in exclusion_stack:
        warnings.start_without_stop(
            lineno, f"{header}_EXCL_START", f"{header}_EXCL_STOP"
        )

    return _make_is_in_any_range(exclude_line_ranges)


def _make_is_in_any_range(ranges: List[Tuple[int, int]]) -> Callable[[int], bool]:
    """
    Create a function to check whether an input is in any range.

    This function should provide reasonable performance
    if queries are mostly made in ascending order.

    Example:
    >>> select = _make_is_in_any_range([(3,4), (5,7)])
    >>> select(0)
    False
    >>> select(6)
    True
    >>> [x for x in range(10) if select(x)]
    [3, 5, 6]
    """

    # values are likely queried in ascending order,
    # allowing the search to start with the first possible range
    ranges = sorted(ranges)
    hint_value = 0
    hint_index = 0

    def is_in_any_range(value: int) -> bool:
        nonlocal hint_value, hint_index

        # if the heuristic failed, restart search from the beginning
        if value < hint_value:
            hint_index = 0

        hint_value = value

        for i in range(hint_index, len(ranges)):
            start, end = ranges[i]
            hint_index = i

            # stop as soon as a too-large range is seen
            if value < start:
                break

            if start <= value < end:
                return True
        else:
            hint_index = len(ranges)

        return False

    return is_in_any_range


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


def _int_from_gcov_unit(formatted: str) -> int:
    """
    Try to reverse gcov's number formatting.

    Gcov's number formatting works like this:

    * if ``decimal_places >= 0``, format a percentage
      * the percentage is fudged so that 0% and 100% are only shown
        when that's the true value
    * otherwise, format a count
      * if human readable numbers are enabled,
        use SI units like ``1.7k`` instead of ``1693``

    Relevant gcov command line flags:

    * ``-c`` enables counts instead of percentages
    * ``-H`` enables human-readable numbers (SI units)

    Note that percentages destroy information: the original value can't be recovered,
    so we must map to zero/one.
    Of course, counts are not that useful either because we don't know the max value.

    Examples:
    >>> _int_from_gcov_unit('123')
    123
    >>> [_int_from_gcov_unit(value) for value in ('17.2%', '0%')]
    [1, 0]
    >>> [_int_from_gcov_unit(value) for value in ('1.7k', '0.5G')]
    [1700, 500000000]
    """
    if formatted.endswith("%"):
        return 1 if float(formatted[:-1]) > 0 else 0

    units = "kMGTPEZY"
    for exponent, unit in enumerate(units, 1):
        if formatted.endswith(unit):
            return int(float(formatted[:-1]) * 1000**exponent)

    return int(formatted)
