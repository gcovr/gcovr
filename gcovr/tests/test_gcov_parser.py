# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

import re
import pytest
import time
from threading import Event

from ..gcov import GcovParser
from ..utils import Logger
from ..workers import Workers

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
    #####:   53:qux();
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
    gcov_8_example_2=GCOV_8_EXAMPLE_2)

GCOV_8_EXPECTED_UNCOVERED_LINES = dict(
    gcov_8_example='33',
    gcov_8_exclude_throw='33',
    nautilus_example='51,53',
    gcov_8_example_2='33')

GCOV_8_EXPECTED_UNCOVERED_BRANCHES = dict(
    gcov_8_example='21,23,24,30,32,33,35',
    gcov_8_exclude_throw='30,32,33',
    nautilus_example='51',
    gcov_8_example_2='21,23,24,30,32,33,35',
)

GCOV_8_EXCLUDE_THROW_BRANCHES = dict(
    gcov_8_exclude_throw=True,
)


@pytest.mark.parametrize('sourcename', sorted(GCOV_8_SOURCES))
def test_gcov_8(capsys, sourcename):
    """Verify support for GCC 8 .gcov files.

    GCC 8 introduces two changes:
    -   for partial lines, the execution count is followed by an asterisk.
    -   instantiations for templates and macros
        are show broken down for each specialization
    """

    source = GCOV_8_SOURCES[sourcename]
    lines = source.splitlines()[1:]
    expected_uncovered_lines = \
        GCOV_8_EXPECTED_UNCOVERED_LINES[sourcename]
    expected_uncovered_branches = \
        GCOV_8_EXPECTED_UNCOVERED_BRANCHES[sourcename]
    exclude_throw_branches = \
        GCOV_8_EXCLUDE_THROW_BRANCHES.get(sourcename, False)

    parser = GcovParser("tmp.cpp", Logger())
    parser.parse_all_lines(
        lines,
        exclude_unreachable_branches=False,
        exclude_throw_branches=exclude_throw_branches,
        ignore_parse_errors=False,
        exclude_lines_by_pattern=None
    )

    covdata = {
        parser.fname: parser.coverage,
    }
    coverage = covdata['tmp.cpp']

    uncovered_lines = coverage.uncovered_lines_str()
    uncovered_branches = coverage.uncovered_branches_str()
    assert uncovered_lines == expected_uncovered_lines
    assert uncovered_branches == expected_uncovered_branches

    out, err = capsys.readouterr()
    assert (out, err) == ('', '')


def contains_phrases(string, *phrases):
    phrase_re = re.compile(
        '.*'.join(re.escape(p) for p in phrases),
        flags=re.DOTALL)
    return bool(phrase_re.search(string))


@pytest.mark.parametrize('ignore_errors', [True, False])
def test_unknown_tags(capsys, ignore_errors):
    source = r"bananas 7 times 3"
    lines = source.splitlines()

    parser = GcovParser("foo.c", Logger())

    def run_the_parser():
        parser.parse_all_lines(
            lines,
            exclude_unreachable_branches=False,
            exclude_throw_branches=False,
            ignore_parse_errors=ignore_errors,
            exclude_lines_by_pattern=None)

    if ignore_errors:
        run_the_parser()
    else:
        with pytest.raises(SystemExit):
            run_the_parser()

    covdata = {
        parser.fname: parser.coverage,
    }
    coverage = covdata['foo.c']

    uncovered_lines = coverage.uncovered_lines_str()
    uncovered_branches = coverage.uncovered_branches_str()
    assert uncovered_lines == ''
    assert uncovered_branches == ''

    out, err = capsys.readouterr()
    assert out == ''
    err_phrases = [
        '(WARNING) Unrecognized GCOV output',
        'bananas',
        'github.com/gcovr/gcovr',
    ]
    if not ignore_errors:
        err_phrases.append('(ERROR) Exiting')
    assert contains_phrases(err, *err_phrases)


def test_pathologic_codeline(capsys):
    source = r": 7:haha"
    lines = source.splitlines()

    parser = GcovParser("foo.c", Logger())
    with pytest.raises(IndexError):
        parser.parse_all_lines(
            lines,
            exclude_unreachable_branches=False,
            exclude_throw_branches=False,
            ignore_parse_errors=False,
            exclude_lines_by_pattern=None)

    out, err = capsys.readouterr()
    assert out == ''
    assert contains_phrases(
        err,
        '(WARNING) Unrecognized GCOV output',
        ': 7:haha',
        'Exception during parsing',
        'IndexError',
        '(ERROR) Exiting',
        'run gcovr with --gcov-ignore-parse-errors')


def check_and_raise(number, mutable, exc_raised, queue_full):
    queue_full.wait()
    if number == 0:
        raise Exception("Number == 0")
    exc_raised.wait()
    mutable.append(None)


@pytest.mark.parametrize('threads', [1, 2, 4, 8])
def test_pathologic_threads(capsys, threads):
    mutable = []
    queue_full = Event()
    exc_raised = Event()
    with pytest.raises(Exception) as excinfo:
        with Workers(threads, lambda: {'mutable': mutable, 'exc_raised': exc_raised, 'queue_full': queue_full}) as pool:
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
