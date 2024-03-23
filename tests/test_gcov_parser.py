# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.2+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
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

# pylint: disable=missing-function-docstring,missing-module-docstring
import logging
import re
import time
import textwrap
from threading import Event
from unittest import mock

import pytest

from gcovr.formats.gcov.parser import NegativeHits, parse_coverage, UnknownLineType
from gcovr.utils import configure_logging
from gcovr.formats.gcov.workers import Workers
from gcovr.exclusions import ExclusionOptions, apply_all_exclusions

configure_logging()


# This example is taken from the GCC 8 Gcov documentation:
# <https://gcc.gnu.org/onlinedocs/gcc/Invoking-Gcov.html>
GCOV_8_EXAMPLE = r"""
        -:    0:Source:tmp.cpp
        -:    0:Graph:tmp.gcno
        -:    0:Data:tmp.gcda
        -:    0:Runs:1
        -:    0:Programs:1
        -:    1:#include <stdio.h>
        -:    2:
        -:    3:template<class T>
        -:    4:class Foo
        -:    5:{
        -:    6:  public:
       1*:    7:  Foo(): b (1000) {}
------------------
Foo<char>::Foo():
function Foo<char>::Foo() called 0 returned 0% blocks executed 0%
    #####:    7:  Foo(): b (1000) {}
------------------
Foo<int>::Foo():
function Foo<int>::Foo() called 1 returned 100% blocks executed 100%
        1:    7:  Foo(): b (1000) {}
------------------
       2*:    8:  void inc () { b++; }
------------------
Foo<char>::inc():
function Foo<char>::inc() called 0 returned 0% blocks executed 0%
    #####:    8:  void inc () { b++; }
------------------
Foo<int>::inc():
function Foo<int>::inc() called 2 returned 100% blocks executed 100%
        2:    8:  void inc () { b++; }
------------------
        -:    9:
        -:   10:  private:
        -:   11:  int b;
        -:   12:};
        -:   13:
        -:   14:template class Foo<int>;
        -:   15:template class Foo<char>;
        -:   16:
        -:   17:int
function main called 1 returned 100% blocks executed 81%
        1:   18:main (void)
        -:   19:{
        -:   20:  int i, total;
        1:   21:  Foo<int> counter;
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        -:   22:
        1:   23:  counter.inc();
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        1:   24:  counter.inc();
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        1:   25:  total = 0;
        -:   26:
       11:   27:  for (i = 0; i < 10; i++)
branch  0 taken 91% (fallthrough)
branch  1 taken 9%
       10:   28:    total += i;
        -:   29:
       1*:   30:  int v = total > 100 ? 1 : 2;
branch  0 taken 0% (fallthrough)
branch  1 taken 100%
        -:   31:
        1:   32:  if (total != 45)
branch  0 taken 0% (fallthrough)
branch  1 taken 100%
    #####:   33:    printf ("Failure\n");
call    0 never executed
branch  1 never executed
branch  2 never executed
        -:   34:  else
        1:   35:    printf ("Success\n");
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        1:   36:  return 0;
        -:   37:}"""

# This example is adapted from #226
# <https://github.com/gcovr/gcovr/issues/226#issuecomment-368226650>
# It is stripped down to the minimum useful testcase.
GCOV_8_NAUTILUS = r"""
        -:    0:Source:../src/nautilus-freedesktop-dbus.c
        -:    0:Graph:/home/user/nautilus/_build/src/nautilus@sta/nautilus-freedesktop-dbus.c.gcno
        -:    0:Data:-
        -:    0:Runs:0
        -:    0:Programs:0
        -:    1:/*
        -:    2: * nautilus-freedesktop-dbus: Implementation for the org.freedesktop DBus file-management interfaces
        -:    3: *
        -:    4: * Nautilus is free software; you can redistribute it and/or
        -:    5: * modify it under the terms of the GNU General Public License as
        -:    6: * published by the Free Software Foundation; either version 2 of the
        -:    7: * License, or (at your option) any later version.
        -:    8: *
        -:    9: * Nautilus is distributed in the hope that it will be useful,
        -:   10: * but WITHOUT ANY WARRANTY; without even the implied warranty of
        -:   11: * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
        -:   12: * General Public License for more details.
        -:   13: *
        -:   14: * You should have received a copy of the GNU General Public License
        -:   15: * along with this program; if not, see <http://www.gnu.org/licenses/>.
        -:   16: *
        -:   17: * Authors: Akshay Gupta <kitallis@gmail.com>
        -:   18: *          Federico Mena Quintero <federico@gnome.org>
        -:   19: */
        -:   50:
    #####:   51:G_DEFINE_TYPE (NautilusFreedesktopDBus, nautilus_freedesktop_dbus, G_TYPE_OBJECT);
------------------
nautilus_freedesktop_dbus_get_type:
function nautilus_freedesktop_dbus_get_type called 0 returned 0% blocks executed 0%
    #####:   51:G_DEFINE_TYPE (NautilusFreedesktopDBus, nautilus_freedesktop_dbus, G_TYPE_OBJECT);
branch  0 never executed
branch  1 never executed
call    2 never executed
branch  3 never executed
branch  4 never executed
branch  5 never executed
branch  6 never executed
call    7 never executed
call    8 never executed
call    9 never executed
------------------
nautilus_freedesktop_dbus_class_intern_init:
function nautilus_freedesktop_dbus_class_intern_init called 0 returned 0% blocks executed 0%
    #####:   51:G_DEFINE_TYPE (NautilusFreedesktopDBus, nautilus_freedesktop_dbus, G_TYPE_OBJECT);
call    0 never executed
branch  1 never executed
branch  2 never executed
call    3 never executed
call    4 never executed
------------------
    #####:   52:foo() ? bar():
        -:   53:  baz();  // above line tests that sections can be terminated
    #####:   54:qux();
"""

# This example is taken from the GCC 8 Gcov documentation:
# <https://gcc.gnu.org/onlinedocs/gcc/Invoking-Gcov.html>
# And modified so that the un-hit for line 7 comes after the
# hit.
GCOV_8_EXAMPLE_2 = r"""
        -:    0:Source:tmp.cpp
        -:    0:Graph:tmp.gcno
        -:    0:Data:tmp.gcda
        -:    0:Runs:1
        -:    0:Programs:1
        -:    1:#include <stdio.h>
        -:    2:
        -:    3:template<class T>
        -:    4:class Foo
        -:    5:{
        -:    6:  public:
       1*:    7:  Foo(): b (1000) {}
------------------
Foo<int>::Foo():
function Foo<int>::Foo() called 1 returned 100% blocks executed 100%
        1:    7:  Foo(): b (1000) {}
------------------
Foo<char>::Foo():
function Foo<char>::Foo() called 0 returned 0% blocks executed 0%
    #####:    7:  Foo(): b (1000) {}
------------------
       2*:    8:  void inc () { b++; }
------------------
Foo<char>::inc():
function Foo<char>::inc() called 0 returned 0% blocks executed 0%
    #####:    8:  void inc () { b++; }
------------------
Foo<int>::inc():
function Foo<int>::inc() called 2 returned 100% blocks executed 100%
        2:    8:  void inc () { b++; }
------------------
        -:    9:
        -:   10:  private:
        -:   11:  int b;
        -:   12:};
        -:   13:
        -:   14:template class Foo<int>;
        -:   15:template class Foo<char>;
        -:   16:
        -:   17:int
function main called 1 returned 100% blocks executed 81%
        1:   18:main (void)
        -:   19:{
        -:   20:  int i, total;
        1:   21:  Foo<int> counter;
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        -:   22:
        1:   23:  counter.inc();
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        1:   24:  counter.inc();
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        1:   25:  total = 0;
        -:   26:
       11:   27:  for (i = 0; i < 10; i++)
branch  0 taken 91% (fallthrough)
branch  1 taken 9%
       10:   28:    total += i;
        -:   29:
       1*:   30:  int v = total > 100 ? 1 : 2;
branch  0 taken 0% (fallthrough)
branch  1 taken 100%
        -:   31:
        1:   32:  if (total != 45)
branch  0 taken 0% (fallthrough)
branch  1 taken 100%
    #####:   33:    printf ("Failure\n");
call    0 never executed
branch  1 never executed
branch  2 never executed
        -:   34:  else
        1:   35:    printf ("Success\n");
call    0 returned 100%
branch  1 taken 100% (fallthrough)
branch  2 taken 0% (throw)
        1:   36:  return 0;
        -:   37:}"""

GCOV_8_SOURCES = dict(
    gcov_8_example=GCOV_8_EXAMPLE,
    gcov_8_exclude_throw=GCOV_8_EXAMPLE,
    nautilus_example=GCOV_8_NAUTILUS,
    gcov_8_example_2=GCOV_8_EXAMPLE_2,
)

GCOV_8_EXPECTED_UNCOVERED_LINES = dict(
    gcov_8_example=[33],
    gcov_8_exclude_throw=[33],
    nautilus_example=[51, 52, 54],
    gcov_8_example_2=[33],
)

GCOV_8_EXPECTED_UNCOVERED_BRANCHES = dict(
    gcov_8_example=[21, 23, 24, 30, 32, 33, 35],
    gcov_8_exclude_throw=[30, 32, 33],
    nautilus_example=[51],
    gcov_8_example_2=[21, 23, 24, 30, 32, 33, 35],
)

GCOV_8_EXCLUDE_THROW_BRANCHES = dict(
    gcov_8_exclude_throw=True,
)


@pytest.mark.parametrize("sourcename", sorted(GCOV_8_SOURCES))
def test_gcov_8(capsys, sourcename):
    """Verify support for GCC 8 .gcov files.

    GCC 8 introduces two changes:
    -   for partial lines, the execution count is followed by an asterisk.
    -   instantiations for templates and macros
        are show broken down for each specialization
    """

    source = GCOV_8_SOURCES[sourcename]
    lines = source.splitlines()
    expected_uncovered_lines = GCOV_8_EXPECTED_UNCOVERED_LINES[sourcename]
    expected_uncovered_branches = GCOV_8_EXPECTED_UNCOVERED_BRANCHES[sourcename]

    coverage, lines = parse_coverage(
        filename="tmp.cpp",
        lines=lines,
        ignore_parse_errors=None,
    )

    apply_all_exclusions(
        coverage,
        lines=lines,
        options=ExclusionOptions(
            exclude_throw_branches=GCOV_8_EXCLUDE_THROW_BRANCHES.get(sourcename, False),
        ),
    )

    uncovered_lines = [
        line.lineno for line in coverage.lines.values() if line.is_uncovered
    ]
    uncovered_branches = [
        line.lineno for line in coverage.lines.values() if line.has_uncovered_branch
    ]
    assert uncovered_lines == expected_uncovered_lines
    assert uncovered_branches == expected_uncovered_branches

    out, err = capsys.readouterr()
    assert (out, err) == ("", "")


def contains_phrases(string, *phrases):
    phrase_re = re.compile(".*".join(re.escape(p) for p in phrases), flags=re.DOTALL)
    return bool(phrase_re.search(string))


@pytest.mark.parametrize("ignore_errors", [True, False])
def test_unknown_tags(caplog, ignore_errors):
    source = r"bananas 7 times 3"
    lines = source.splitlines()

    def run_the_parser():
        coverage, _ = parse_coverage(
            filename="foo.c",
            lines=lines,
            ignore_parse_errors=set(["all"]) if ignore_errors else None,
        )
        return coverage

    if ignore_errors:
        coverage = run_the_parser()

        uncovered_lines = [
            line.lineno for line in coverage.lines.values() if line.is_uncovered
        ]
        uncovered_branches = [
            line.lineno for line in coverage.lines.values() if line.has_uncovered_branch
        ]
        assert uncovered_lines == []
        assert uncovered_branches == []
    else:
        with pytest.raises(Exception):
            coverage = run_the_parser()

    messages = caplog.record_tuples
    message0 = messages[0]
    assert message0[1] == logging.WARNING
    err_phrases = [
        "Unrecognized GCOV output",
        "bananas",
        "github.com/gcovr/gcovr",
    ]
    assert contains_phrases(message0[2], *err_phrases)
    if not ignore_errors:
        message = messages[2]
        assert message[1] == logging.ERROR
        assert "Exiting" in message[2]


def test_pathologic_codeline(caplog):
    source = r": 7:haha"
    lines = source.splitlines()

    with pytest.raises(UnknownLineType):
        parse_coverage(
            filename="foo.c",
            lines=lines,
            ignore_parse_errors=None,
        )

    messages = caplog.record_tuples
    message0 = messages[0]
    assert message0[1] == logging.WARNING
    warning_phrases1 = [
        "Unrecognized GCOV output",
        ": 7:haha",
    ]
    assert contains_phrases(message0[2], *warning_phrases1)

    message = messages[1]
    assert message[1] == logging.WARNING
    warning_phrases2 = [
        "Exception during parsing",
        "UnknownLineType",
    ]
    assert contains_phrases(message[2], *warning_phrases2)

    message = messages[2]
    assert message[1] == logging.ERROR
    error_phrases = [
        "Exiting",
        "run gcovr with --gcov-ignore-parse-errors",
    ]
    assert contains_phrases(message[2], *error_phrases)


def test_exception_during_coverage_processing(caplog):
    """
    This cannot happen during normal processing, but as a defense against
    unexpected changes to the format the ``--gcov-ignore-parse-errors`` option
    will try to catch as many errors as possible. In order to inject a testable
    fault, merging of coverage data will be mocked.
    """

    source = textwrap.dedent(
        r"""
    function __compiler-internal called 5 returned 6 blocks executed 7%
          1: 3:magic code!
    branch 0 taken 5%
      #####: 4:recover here
    """
    )
    lines = source.splitlines()

    with mock.patch("gcovr.formats.gcov.parser.insert_function_coverage") as m:
        m.side_effect = AssertionError("totally broken")
        with pytest.raises(AssertionError) as ex_info:
            parse_coverage(
                lines,
                filename="test.cpp",
                ignore_parse_errors=None,
            )

    # check that this is our exception
    assert ex_info.value.args[0] == "totally broken"

    messages = caplog.record_tuples
    message0 = messages[0]
    assert message0[1] == logging.WARNING
    warning_phrases1 = [
        "Unrecognized GCOV output",
        lines[0],
    ]
    assert contains_phrases(message0[2], *warning_phrases1)

    message = messages[1]
    assert message[1] == logging.WARNING
    warning_phrases2 = [
        "Exception during parsing",
        "AssertionError",
    ]
    assert contains_phrases(message[2], *warning_phrases2)

    message = messages[2]
    assert message[1] == logging.ERROR
    error_phrases = [
        "Exiting",
        "run gcovr with --gcov-ignore-parse-errors",
    ]
    assert contains_phrases(message[2], *error_phrases)


def test_trailing_function_tag():
    """
    This cannot occur in real gcov, but the parser should be robust enough to
    handle it.
    """

    source = textwrap.dedent(
        """\
      #####: 2:example line
    function example called 17 returned 16 blocks executed 3%
    """
    )

    coverage, _ = parse_coverage(
        source.splitlines(),
        filename="test.cpp",
        ignore_parse_errors=None,
    )

    assert coverage.functions.keys() == {"example"}
    fcov = coverage.functions["example"]
    assert list(fcov.count.keys()) == [3]  # previous lineno + 1
    assert fcov.name == "example"
    assert fcov.count[3] == 17  # number of calls


@pytest.mark.parametrize(
    "flags",
    [
        "none",
        "exclude_unreachable_branches",
        "exclude_throw_branches",
        "exclude_unreachable_branches,exclude_throw_branches",
    ],
)
def test_branch_exclusion(flags):
    """
    On some lines, branch coverage may be discarded.
    """

    source = textwrap.dedent(
        """\
          1: 1: normal line
        branch 1 taken 80%
          1: 2: } // line without apparent code
        branch 2 taken 70%
          1: 3: exception-only code
        branch 3 taken 60% (throw)
          1: 4: } // no code and throw
        branch 4 taken 50% (throw)
        """
    )

    expected_covered_branches = {1, 2, 3, 4}
    if "exclude_throw_branches" in flags:
        expected_covered_branches -= {3, 4}
    if "exclude_unreachable_branches" in flags:
        expected_covered_branches -= {2, 4}

    coverage, lines = parse_coverage(
        source.splitlines(),
        filename="example.cpp",
        ignore_parse_errors=None,
    )

    apply_all_exclusions(
        coverage,
        lines=lines,
        options=ExclusionOptions(
            exclude_throw_branches=("exclude_throw_branches" in flags),
            exclude_unreachable_branches=("exclude_unreachable_branches" in flags),
        ),
    )

    covered_branches = {
        branch for line in coverage.lines.values() for branch in line.branches.keys()
    }

    assert covered_branches == expected_covered_branches


def test_negativ_branch_count():
    """
    A exception shall be raised.
    """

    source = textwrap.dedent(
        """\
          1: 1: normal line
        branch 1 taken 80%
          1: 2: } // line without apparent code
        branch 2 taken -11234
          1: 3: exception-only code
        branch 3 taken 60% (throw)
        """
    )

    with pytest.raises(NegativeHits):
        parse_coverage(
            source.splitlines(),
            filename="example.cpp",
            ignore_parse_errors=None,
        )


def test_negative_line_count_ignored():
    """
    A exception shall be raised.
    """

    source = textwrap.dedent(
        """\
             1: 1:foo += 1;
            -1: 2:foo += 1;
             2: 3:foo += 1;
        """
    )

    coverage, _ = parse_coverage(
        source.splitlines(),
        filename="example.cpp",
        ignore_parse_errors=set(["negative_hits.warn"]),
    )

    covered_lines = {line.lineno for line in coverage.lines.values() if line.is_covered}

    assert covered_lines == {1, 3}


def test_negative_branch_count_ignored():
    """
    A exception shall be raised.
    """

    source = textwrap.dedent(
        """\
          1: 1: normal line
        branch 1 taken 80%
          1: 2: } // line without apparent code
        branch 2 taken -11234
          1: 3: exception-only code
        branch 3 taken 60% (throw)
        """
    )

    coverage, _ = parse_coverage(
        source.splitlines(),
        filename="example.cpp",
        ignore_parse_errors=set(["negative_hits.warn"]),
    )

    covered_branches = {
        branch
        for line in coverage.lines.values()
        for branch in line.branches.keys()
        if line.branches[branch].is_covered
    }

    assert covered_branches == {1, 3}


@pytest.mark.parametrize("flags", ["none", "exclude_internal_functions"])
def test_function_exclusion(flags):
    """
    Compiler-generated function names can be excluded.
    """

    source = textwrap.dedent(
        """\
        function __foo called 5 returned 50% blocks executed 70%
          12: 5:void __foo() {
        """
    )

    if "exclude_internal_functions" in flags:
        expected_functions = []
    else:
        expected_functions = ["__foo"]

    coverage, lines = parse_coverage(
        source.splitlines(),
        filename="example.cpp",
        ignore_parse_errors=None,
    )

    apply_all_exclusions(
        coverage,
        lines=lines,
        options=ExclusionOptions(
            exclude_internal_functions=("exclude_internal_functions" in flags),
        ),
    )

    functions = list(coverage.functions.keys())

    assert functions == expected_functions


def test_noncode_lines():
    """
    Verify how noncode status is used.

    Gcov marks some lines as not containing any coverage data::

        -: 42: // no code

    But gcovr can also exclude additional lines as noncode.
    """

    def get_line_status(
        lines: list,
        *,
        exclude_function_lines: bool = False,
        exclude_noncode_lines: bool = False,
    ):
        coverage, source = parse_coverage(
            lines,
            filename="example.cpp",
            ignore_parse_errors=None,
        )

        options = ExclusionOptions(
            exclude_function_lines=exclude_function_lines,
            exclude_noncode_lines=exclude_noncode_lines,
        )
        apply_all_exclusions(coverage, lines=source, options=options)

        for line_data in coverage.lines.values():
            return f"normal:{line_data.count}"

        return "noncode"

    # First, handling of function lines

    # By itself, function lines have no special treatment.
    status = get_line_status(["3: 32:void foo(){}"])
    assert status == "normal:3"

    # If gcov reports a function, keep the line.
    status = get_line_status(
        ["function foo called 3 returned 99% blocks executed 70%", "3: 32:void foo(){}"]
    )
    assert status == "normal:3"

    # But if EXCLUDE_FUNCTION_LINES is enabled, discard the line.
    status = get_line_status(
        [
            "function foo called 3 returned 99% blocks executed 70%",
            "3: 32:void foo(){}",
        ],
        exclude_function_lines=True,
    )
    assert status == "noncode"

    # Next, handling of noncode lines

    # Gcov says noncode but it looks like code: throw line away
    assert get_line_status(["-: 32:this looks like code"]) == "noncode"

    # Gcov says noncode and it doesn't look like code: discard
    assert get_line_status(["-: 32:}"]) == "noncode"

    # Uncovered line with code: keep
    assert get_line_status(["#####: 32:looks like code"]) == "normal:0"

    # Uncovered code that doesn't look like code: discard
    assert get_line_status(["#####: 32:}"], exclude_noncode_lines=True) == "noncode"


def check_and_raise(number, mutable, exc_raised, queue_full):
    queue_full.wait()
    if number == 0:
        raise Exception("Number == 0")
    exc_raised.wait()
    mutable.append(None)


@pytest.mark.parametrize("threads", [1, 2, 4, 8])
def test_pathologic_threads(threads):
    mutable = []
    queue_full = Event()
    exc_raised = Event()
    with pytest.raises(Exception) as excinfo:
        with Workers(
            threads,
            lambda: {
                "mutable": mutable,
                "exc_raised": exc_raised,
                "queue_full": queue_full,
            },
        ) as pool:
            for extra in range(0, 10000):
                pool.add(check_and_raise, extra)

            # Queue is filled
            queue_full.set()

            # Wait until the exception has been completed
            while not pool.exceptions:
                # Yield to the worker threads
                time.sleep(0)

            # Queue should be drained and exception raised
            exc_raised.set()
            pool.wait()

    # Outer level catches correct exception
    assert excinfo.value.args[0] == "Number == 0"

    # At most (threads - 1) appends can take place as the
    # first job throws an exception and every other thread
    # can action at most one job before the queue is drained
    assert len(mutable) <= threads - 1
