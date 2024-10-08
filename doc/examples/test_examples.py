# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.0+main, a parsing and reporting tool for gcov.
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

import glob
import os
import platform
import pytest
import subprocess  # nosec # Commands are trusted.

from tests.test_gcovr import SCRUBBERS, assert_equals

IS_MACOS = platform.system() == "Darwin"

data_dirname = os.path.dirname(os.path.abspath(__file__))


class Example(object):
    def __init__(self, name, format, script, baseline):
        self.name = name
        self.format = format
        self.script = script
        self.baseline = baseline

    def __str__(self):
        return os.path.basename(self.baseline)


def is_compiler(actual: str, *expected: str) -> bool:
    return any(compiler in actual for compiler in expected)


def find_test_cases():
    if platform.system() == "Windows":
        return
    for script in glob.glob(data_dirname + "/*.sh"):
        basename = os.path.basename(script)
        name, _ = os.path.splitext(basename)
        for format in "txt cobertura csv json html".split():
            if format in ("html", "cobertura") and is_compiler(
                os.getenv("CC"), "gcc-5", "gcc-6", "gcc-14"
            ):
                continue
            baseline = "{data_dirname}/{name}.{ext}".format(
                data_dirname=data_dirname,
                name=name,
                ext="xml" if format == "cobertura" else format,
            )
            if not os.path.exists(baseline):
                continue
            else:
                yield Example(name, format, script, baseline)


@pytest.mark.skipif(
    not os.path.split(os.getenv("CC"))[1].startswith("gcc") or IS_MACOS,
    reason="Only for gcc",
)
@pytest.mark.parametrize("example", find_test_cases(), ids=str)
def test_example(example):
    cmd = example.script
    baseline_file = example.baseline
    scrub = SCRUBBERS[example.format]
    # Read old file
    with open(  # nosemgrep # It's intended to use the local
        baseline_file, newline=""
    ) as f:
        baseline = scrub(f.read())

    start_dirname = os.getcwd()
    os.chdir(data_dirname)
    subprocess.run(cmd)  # nosec # The command is not a user input
    with open(  # nosemgrep # It's intended to use the local
        baseline_file, newline=""
    ) as f:
        current = scrub(f.read())
    current = scrub(current)

    assert_equals(baseline_file, baseline, "<STDOUT>", current, encoding="utf8")
    os.chdir(start_dirname)


def test_timestamps_example():
    subprocess.check_call(  # nosec # We run on several system and do not know the full path
        ["sh", "example_timestamps.sh"], cwd=data_dirname
    )
