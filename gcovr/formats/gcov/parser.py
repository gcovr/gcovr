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
Handle parsing of the textual ``.gcov`` file format.

Other modules should only use the following items:
`parse_metadata()`, `parse_coverage()`, `UnknownLineType`.

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
    Any,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Pattern,
    Set,
    Tuple,
    Union,
)

from gcovr.utils import get_md5_hexdigest

from ...coverage import (
    BranchCoverage,
    FileCoverage,
    FunctionCoverage,
    CallCoverage,
    LineCoverage,
)
from ...merging import (
    FUNCTION_MAX_LINE_MERGE_OPTIONS,
    insert_branch_coverage,
    insert_function_coverage,
    insert_line_coverage,
    insert_call_coverage,
)


LOGGER = logging.getLogger("gcovr")
SUSPICIOUS_COUNTER = 2**32


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
    pattern = pattern.replace(" ", r" +")
    pattern = pattern.replace("INT", r"[0-9]+")
    pattern = pattern.replace("VALUE", r"(?:NAN %|-?[0-9.]+[%kMGTPEZY]?)")
    return re.compile("^" + pattern + "$")


_RE_FUNCTION_LINE = _line_pattern(
    r"function (.*?) called (INT) returned (VALUE) blocks executed (VALUE)"
)
_RE_BRANCH_LINE = _line_pattern(
    r"branch (INT) (?:taken (VALUE)|never executed)(?: \((\w+)\))?"
)
_RE_CALL_LINE = _line_pattern(r"call (INT) (?:returned (VALUE)|never executed)")
_RE_UNCONDITIONAL_LINE = _line_pattern(
    r"unconditional (INT) (?:taken (VALUE)|never executed)"
)
_RE_SOURCE_LINE = _line_pattern(r"(?: )?(VALUE[*]?|-|[#]{5}|[=]{5}):(?: )?(INT):(.*)")
_RE_BLOCK_LINE = _line_pattern(r"(?: )?(VALUE|[$]{5}|[%]{5}):(?: )?(INT)-block (INT)")


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
    value: Optional[str]


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

    ``function NAME called COUNT returned RETURNED blocks executed BLOCKS``
    """

    name: str
    count: int
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


class NegativeHits(Exception):
    """Used to signal that a negative count value was found."""

    def __init__(self, line: str) -> None:
        super().__init__(
            f"Got negative hit value in gcov line {line!r} caused by a\n"
            "bug in gcov tool, see\n"
            "https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option\n"
            "--gcov-ignore-parse-errors with a value of negative_hits.warn,\n"
            "or negative_hits.warn_once_per_file."
        )

    @staticmethod
    def raise_if_not_ignored(
        line, ignore_parse_errors: set, persistent_states: dict
    ) -> None:
        """Raise exception if not ignored by options"""
        if ignore_parse_errors is not None and any(
            [
                v in ignore_parse_errors
                for v in [
                    "all",
                    "negative_hits.warn",
                    "negative_hits.warn_once_per_file",
                ]
            ]
        ):
            if "negative_hits.warn_once_per_file" in persistent_states:
                persistent_states["negative_hits.warn_once_per_file"] += 1
            else:
                LOGGER.warning(f"Ignoring negative hits in line {line!r}.")
                if "negative_hits.warn_once_per_file" in ignore_parse_errors:
                    persistent_states["negative_hits.warn_once_per_file"] = 1
        else:
            raise NegativeHits(line)


class SuspiciousHits(Exception):
    """Used to signal that a negative count value was found."""

    def __init__(self, line: str) -> None:
        super().__init__(
            f"Got suspicious hit value in gcov line {line!r} caused by a\n"
            "bug in gcov tool, see\n"
            "https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080. Use option\n"
            "--gcov-ignore-parse-errors with a value of suspicious_hits.warn,\n"
            "or suspicious_hits.warn_once_per_file."
        )

    @staticmethod
    def raise_if_not_ignored(
        line, ignore_parse_errors: set, persistent_states: dict
    ) -> None:
        """Raise exception if not ignored by options"""
        if ignore_parse_errors is not None and any(
            [
                v in ignore_parse_errors
                for v in [
                    "all",
                    "suspicious_hits.warn",
                    "suspicious_hits.warn_once_per_file",
                ]
            ]
        ):
            if "suspicious_hits.warn_once_per_file" in persistent_states:
                persistent_states["suspicious_hits.warn_once_per_file"] += 1
            else:
                LOGGER.warning(f"Ignoring suspicious hits in line {line!r}.")
                if "suspicious_hits.warn_once_per_file" in ignore_parse_errors:
                    persistent_states["suspicious_hits.warn_once_per_file"] = 1
        else:
            raise SuspiciousHits(line)


def parse_metadata(lines: List[str]) -> Dict[str, Optional[str]]:
    r"""
    Collect the header/metadata lines from a gcov file.

    Example:
    >>> parse_metadata('''
    ...   -: 0:Foo:bar
    ...   -: 0:Key:123
    ... '''.splitlines())
    Traceback (most recent call last):
       ...
    RuntimeError: Missing key 'Source' in metadata. GCOV data was >>
      -: 0:Foo:bar
      -: 0:Key:123<< End of GCOV data
    >>> parse_metadata('-: 0:Source: file \n -: 0:Foo: bar \n -: 0:Key: 123 '.splitlines())
    {'Source': 'file', 'Foo': 'bar', 'Key': '123'}
    >>> parse_metadata('''
    ...   -: 0:Source:file
    ...   -: 0:Foo:bar
    ...   -: 0:Key
    ... '''.splitlines())
    {'Source': 'file', 'Foo': 'bar', 'Key': None}
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

    if "Source" not in collected:
        data = "\n".join(lines)
        raise RuntimeError(
            f"Missing key 'Source' in metadata. GCOV data was >>{data}<< End of GCOV data"
        )

    return collected


_LineWithError = Tuple[str, Exception]


def parse_coverage(
    lines: List[str],
    *,
    filename: str,
    ignore_parse_errors: Set,
) -> Tuple[FileCoverage, List[str]]:
    """
    Extract coverage data from a gcov report.

    Logging:
    Parse problems are reported as warnings.
    Coverage exclusion decisions are reported as verbose messages.

    Arguments:
        lines: the lines of the file to be parsed (excluding newlines)
        filename: for error reports
        ignore_parse_errors: which errors should be converted to warnings

    Returns:
        tuple of the coverage data and the source code lines

    Raises:
        Any exceptions during parsing, unless ignore_parse_errors is set.
    """

    lines_with_errors: List[_LineWithError] = []
    tokenized_lines: List[Tuple[_Line, str]] = []
    persistent_states: Dict[str, Any] = {}
    for raw_line in lines:

        # empty lines shouldn't occur in reality, but are common in testing
        if not raw_line:
            continue

        try:
            tokenized_lines.append(
                (
                    _parse_line(raw_line, ignore_parse_errors, persistent_states),
                    raw_line,
                )
            )
        except Exception as ex:  # pylint: disable=broad-except
            lines_with_errors.append((raw_line, ex))

    if (
        "negative_hits.warn_once_per_file" in persistent_states
        and persistent_states["negative_hits.warn_once_per_file"] > 1
    ):
        LOGGER.warning(
            f"Ignored {persistent_states['negative_hits.warn_once_per_file']} negative hits overall."
        )

    if (
        "suspicious_hits.warn_once_per_file" in persistent_states
        and persistent_states["suspicious_hits.warn_once_per_file"] > 1
    ):
        LOGGER.warning(
            f"Ignored {persistent_states['suspicious_hits.warn_once_per_file']} suspicious hits overall."
        )

    coverage = FileCoverage(filename)
    state = _ParserState()
    for line, raw_line in tokenized_lines:
        try:
            state = _gather_coverage_from_line(
                state,
                line,
                coverage=coverage,
            )
        except Exception as ex:  # pylint: disable=broad-except
            lines_with_errors.append((raw_line, ex))
            state = _ParserState(is_recovering=True)

    # Clean up the final state. This shouldn't happen,
    # but the last line could theoretically contain pending function lines
    for function in state.deferred_functions:
        name, count, blocks = function
        insert_function_coverage(
            coverage,
            FunctionCoverage(
                None,
                name,
                lineno=state.lineno + 1,
                count=count,
                blocks=blocks,
            ),
            FUNCTION_MAX_LINE_MERGE_OPTIONS,
        )

    _report_lines_with_errors(
        lines_with_errors,
        filename=filename,
        ignore_parse_errors=ignore_parse_errors,
    )

    src_lines = _reconstruct_source_code(line for line, _ in tokenized_lines)

    return coverage, src_lines


def _reconstruct_source_code(tokens: Iterable[_Line]) -> List[str]:
    source_token_lines = [line for line in tokens if isinstance(line, _SourceLine)]

    src_lines = [""] * max((line.lineno for line in source_token_lines), default=0)
    for line in source_token_lines:
        src_lines[line.lineno - 1] = line.source_code

    return src_lines


class _ParserState(NamedTuple):
    deferred_functions: List[_FunctionLine] = []
    lineno: int = 0
    blockno: int = None
    line_contents: str = ""
    is_recovering: bool = False


def _gather_coverage_from_line(
    state: _ParserState,
    line: _Line,
    *,
    coverage: FileCoverage,
) -> _ParserState:
    """
    Interpret a Line, updating the FileCoverage, and transitioning ParserState.

    The function handles all possible Line variants, and dies otherwise:
    >>> _gather_coverage_from_line(_ParserState(), "illegal line type", coverage=...)
    Traceback (most recent call last):
    AssertionError: Unexpected line type: 'illegal line type'
    """
    # pylint: disable=too-many-return-statements,too-many-branches
    # pylint: disable=no-else-return  # make life easier for type checkers

    if isinstance(line, _SourceLine):
        raw_count, lineno, source_code, extra_info = line

        is_noncode = extra_info & _ExtraInfo.NONCODE

        if not is_noncode:
            insert_line_coverage(
                coverage,
                LineCoverage(
                    lineno,
                    count=raw_count,
                    md5=get_md5_hexdigest(source_code.encode("utf-8")),
                ),
            )

        # handle deferred functions
        for function in state.deferred_functions:
            name, count, blocks = function

            insert_function_coverage(
                coverage,
                FunctionCoverage(None, name, lineno=lineno, count=count, blocks=blocks),
                FUNCTION_MAX_LINE_MERGE_OPTIONS,
            )

        return _ParserState(
            lineno=line.lineno,
            line_contents=line.source_code,
            blockno=state.blockno,
        )

    elif state.is_recovering:
        return state  # skip until the next _SourceLine

    elif isinstance(line, _FunctionLine):
        # Defer handling of the function tag until the next source line.
        # This is important to get correct line number information.
        return state._replace(deferred_functions=[*state.deferred_functions, line])

    elif isinstance(line, _BranchLine):
        branchno, hits, annotation = line

        # line_cov won't exist if it was considered noncode
        line_cov = coverage.lines.get(state.lineno)

        if line_cov:
            insert_branch_coverage(
                line_cov,
                branchno,
                BranchCoverage(
                    blockno=state.blockno,
                    count=hits,
                    fallthrough=(annotation == "fallthrough"),
                    throw=(annotation == "throw"),
                ),
            )

        return state

    # ignore metadata in this phase
    elif isinstance(line, _MetadataLine):
        return state

    # currently, the parser just ignores specialization sections
    elif isinstance(line, (_SpecializationMarkerLine, _SpecializationNameLine)):
        return state

    # ignore unused line types, such as specialization sections
    elif isinstance(line, _CallLine):
        callno, returned = line
        line_cov = coverage.lines[state.lineno]  # must already exist

        insert_call_coverage(
            line_cov,
            CallCoverage(
                callno=callno,
                covered=(returned > 0),
            ),
        )

        return state

    elif isinstance(line, _BlockLine):
        _, _, blockno, _ = line
        return state._replace(blockno=blockno)

    elif isinstance(line, (_UnconditionalLine,)):
        return state

    raise AssertionError(f"Unexpected line type: {line!r}")


def _report_lines_with_errors(
    lines_with_errors: List[_LineWithError],
    *,
    filename: str,
    ignore_parse_errors: set,
) -> None:
    """Log warnings and potentially re-throw exceptions"""

    if not lines_with_errors:
        return

    lines = [line for line, _ in lines_with_errors]
    errors = [error for _, error in lines_with_errors]

    lines_output = "\n\t  ".join(lines)
    LOGGER.warning(
        f"Unrecognized GCOV output for {filename}\n"
        f"\t  {lines_output}\n"
        "\tThis is indicative of a gcov output parse error.\n"
        "\tPlease report this to the gcovr developers\n"
        "\tat <https://github.com/gcovr/gcovr/issues>."
    )

    for ex in errors:
        LOGGER.warning(f"Exception during parsing:\n\t{type(ex).__name__}: {ex}")

    if ignore_parse_errors is not None and "all" in ignore_parse_errors:
        return

    LOGGER.error(
        "Exiting because of parse errors.\n"
        "\tYou can run gcovr with --gcov-ignore-parse-errors=...\n"
        "\tto continue anyway."
    )

    # if we caught an exception, re-raise it for the traceback
    raise errors[0]  # guaranteed to have at least one exception


def _parse_line(
    line: str, ignore_parse_errors: set = (), persistent_states: dict = {}
) -> _Line:
    """
    Categorize/parse individual lines without further processing.

    Example: can parse code line:
    >>> _parse_line('     -: 13:struct Foo{};')
    _SourceLine(hits=0, lineno=13, source_code='struct Foo{};', extra_info=NONCODE)
    >>> _parse_line('    12: 13:foo += 1;  ')
    _SourceLine(hits=12, lineno=13, source_code='foo += 1;  ', extra_info=NONE)
    >>> _parse_line(' #####: 13:foo += 1;')
    _SourceLine(hits=0, lineno=13, source_code='foo += 1;', extra_info=NONE)
    >>> _parse_line(' #####:10000:foo += 1;')  # see https://github.com/gcovr/gcovr/issues/882
    _SourceLine(hits=0, lineno=10000, source_code='foo += 1;', extra_info=NONE)
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
    >>> _parse_line('branch 3 taken -1', ("negative_hits.warn",))
    _BranchLine(branchno=3, hits=0, annotation=None)
    >>> _parse_line('branch 3 taken 4294967296', ("suspicious_hits.warn",))
    _BranchLine(branchno=3, hits=0, annotation=None)
    >>> _parse_line('branch 7 taken 3% (fallthrough)')
    _BranchLine(branchno=7, hits=1, annotation='fallthrough')
    >>> _parse_line('branch 17 taken 99% (throw)')
    _BranchLine(branchno=17, hits=1, annotation='throw')
    >>> _parse_line('branch  0 never executed')
    _BranchLine(branchno=0, hits=0, annotation=None)
    >>> _parse_line('branch  0 never executed (fallthrough)')
    _BranchLine(branchno=0, hits=0, annotation='fallthrough')
    >>> _parse_line('branch 2 with some unknown format')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType: branch 2 with some unknown format

    Example: can parse call tags:
    >>> _parse_line('call  0 never executed')
    _CallLine(callno=0, returned=0)
    >>> _parse_line('call  17 returned 50%')
    _CallLine(callno=17, returned=1)
    >>> _parse_line('call  17 returned 9')
    _CallLine(callno=17, returned=9)
    >>> _parse_line('call 2 with some unknown format')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType: call 2 with some unknown format

    Example: can parse unconditional branches
    >>> _parse_line('unconditional 1 taken 17')
    _UnconditionalLine(branchno=1, hits=17)
    >>> _parse_line('unconditional 2 taken -1', ignore_parse_errors=set(['negative_hits.warn']))
    _UnconditionalLine(branchno=2, hits=0)
    >>> _parse_line('unconditional 2 taken 4294967296', ignore_parse_errors=set(['suspicious_hits.warn']))
    _UnconditionalLine(branchno=2, hits=0)
    >>> _parse_line('unconditional 3 never executed')
    _UnconditionalLine(branchno=3, hits=0)
    >>> _parse_line('unconditional with some unknown format')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType: unconditional with some unknown format

    Example: can parse function tags:
    >>> _parse_line('function foo called 2 returned 1 blocks executed 85%')
    _FunctionLine(name='foo', count=2, blocks_covered=85.0)
    >>> _parse_line('function foo called 2 returned 50% blocks executed 85%')
    _FunctionLine(name='foo', count=2, blocks_covered=85.0)
    >>> _parse_line('function foo called 2 returned 100% blocks executed 85%')
    _FunctionLine(name='foo', count=2, blocks_covered=85.0)
    >>> _parse_line('function foo with some unknown format')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType: function foo with some unknown format

    Example: can parse template specialization markers:
    >>> _parse_line('------------------')
    _SpecializationMarkerLine()

    Example: can parse template specialization names:
    >>> _parse_line('Foo<bar>::baz():')
    _SpecializationNameLine(name='Foo<bar>::baz()')
    >>> _parse_line(' foo:')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType:  foo:
    >>> _parse_line(':')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType: :

    Example: can parse block line:
    >>> _parse_line('     1: 32-block  0')
    _BlockLine(hits=1, lineno=32, blockno=0, extra_info=NONE)
    >>> _parse_line(' %%%%%: 33-block  1')
    _BlockLine(hits=0, lineno=33, blockno=1, extra_info=NONE)
    >>> _parse_line(' $$$$$: 33-block  1')
    _BlockLine(hits=0, lineno=33, blockno=1, extra_info=EXCEPTION_ONLY)
    >>> _parse_line(' %%%%%:10000-block  0')  # see https://github.com/gcovr/gcovr/issues/882
    _BlockLine(hits=0, lineno=10000, blockno=0, extra_info=NONE)
    >>> _parse_line('     -1: 32-block  0', ignore_parse_errors=set(['negative_hits.warn']))
    _BlockLine(hits=0, lineno=32, blockno=0, extra_info=NONE)
    >>> _parse_line('     4294967296: 32-block  0', ignore_parse_errors=set(['suspicious_hits.warn']))
    _BlockLine(hits=0, lineno=32, blockno=0, extra_info=NONE)
    >>> _parse_line('     1: 9-block with some unknown format')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType:      1: 9-block with some unknown format

    Example: will reject garbage:
    >>> _parse_line('nonexistent_tag foo bar')
    Traceback (most recent call last):
    gcovr.formats.gcov.parser.UnknownLineType: nonexistent_tag foo bar
    """
    # pylint: disable=too-many-branches

    tag = _parse_tag_line(line, ignore_parse_errors, persistent_states)
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
        hits_str, lineno, source_code = match.groups()

        # METADATA (key, value)
        if hits_str == "-" and lineno == "0":
            if ":" in source_code:
                key, value = source_code.split(":", 1)
                return _MetadataLine(key, value.strip())
            else:
                # Add a synthetic metadata with no value
                return _MetadataLine(source_code, None)

        if hits_str == "-":
            hits = 0
            extra_info = _ExtraInfo.NONCODE
        elif hits_str == "#####":
            hits = 0
            extra_info = _ExtraInfo.NONE
        elif hits_str == "=====":
            hits = 0
            extra_info = _ExtraInfo.EXCEPTION_ONLY
        elif hits_str.endswith("*"):
            hits = _int_from_gcov_unit(hits_str[:-1])
            extra_info = _ExtraInfo.PARTIAL
        else:
            hits = _int_from_gcov_unit(hits_str)
            extra_info = _ExtraInfo.NONE

        if hits < 0:
            NegativeHits.raise_if_not_ignored(
                line, ignore_parse_errors, persistent_states
            )
            hits = 0

        if hits >= SUSPICIOUS_COUNTER:
            SuspiciousHits.raise_if_not_ignored(
                line, ignore_parse_errors, persistent_states
            )
            hits = 0

        return _SourceLine(hits, int(lineno), source_code, extra_info)

    # BLOCK
    #
    # Structure: "COUNT: LINENO-block BLOCKNO"
    if "-block " in line:
        match = _RE_BLOCK_LINE.match(line)
        if match is not None:
            hits_str, lineno, blockno = match.groups()

            if hits_str == "%%%%%":
                hits = 0
                extra_info = _ExtraInfo.NONE
            elif hits_str == "$$$$$":
                hits = 0
                extra_info = _ExtraInfo.EXCEPTION_ONLY
            else:
                hits = _int_from_gcov_unit(hits_str)
                extra_info = _ExtraInfo.NONE

            if hits < 0:
                NegativeHits.raise_if_not_ignored(
                    line, ignore_parse_errors, persistent_states
                )
                hits = 0

            if hits >= SUSPICIOUS_COUNTER:
                SuspiciousHits.raise_if_not_ignored(
                    line, ignore_parse_errors, persistent_states
                )
                hits = 0

            return _BlockLine(hits, int(lineno), int(blockno), extra_info)

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


def _parse_tag_line(
    line: str, ignore_parse_errors: set = (), persistent_states: dict = {}
) -> Optional[_Line]:
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

            if hits < 0:
                NegativeHits.raise_if_not_ignored(
                    line, ignore_parse_errors, persistent_states
                )
                hits = 0

            if hits >= SUSPICIOUS_COUNTER:
                SuspiciousHits.raise_if_not_ignored(
                    line, ignore_parse_errors, persistent_states
                )
                hits = 0

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
            hits = 0 if taken_str is None else _int_from_gcov_unit(taken_str)

            if hits < 0:
                NegativeHits.raise_if_not_ignored(
                    line, ignore_parse_errors, persistent_states
                )
                hits = 0

            if hits >= SUSPICIOUS_COUNTER:
                SuspiciousHits.raise_if_not_ignored(
                    line, ignore_parse_errors, persistent_states
                )
                hits = 0

            return _UnconditionalLine(int(branch_id), hits)

    # FUNCTION
    #
    # Structure:
    # function NAME called VALUE returned VALUE blocks executed VALUE
    if line.startswith("function "):
        match = _RE_FUNCTION_LINE.match(line)
        if match is not None:
            name, count, _, blocks = match.groups()
            count = _int_from_gcov_unit(count)

            return _FunctionLine(
                name,
                count,
                _float_from_gcov_percent(blocks),
            )

    # SPECIALIZATION MARKER
    #
    # Structure: literally just lots of hyphens
    if line.startswith("-----"):
        return _SpecializationMarkerLine()

    return None


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
    >>> _int_from_gcov_unit('-1.2k')
    -1200
    >>> [_int_from_gcov_unit(value) for value in ('NAN %', '17.2%', '0%')]
    [0, 1, 0]
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


def _float_from_gcov_percent(formatted: str) -> int:
    """
    Transform percentage to float value

    Examples:
    >>> [_float_from_gcov_percent(value) for value in ('NAN %', '17.2%', '0%')]
    [nan, 17.2, 0.0]
    """

    if not formatted.endswith("%"):
        raise AssertionError(f"Number must end with %, got {formatted}")

    return float(formatted[:-1])
