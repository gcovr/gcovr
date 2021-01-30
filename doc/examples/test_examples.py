# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 4.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import glob
import os
import pytest
import subprocess
import sys

from gcovr.tests.test_gcovr import SCRUBBERS, ASSERT_EQUALS

datadir = os.path.dirname(os.path.abspath(__file__))


class Example(object):
    def __init__(self, name, script, baseline):
        self.name = name
        self.script = script
        self.baseline = baseline

    def __str__(self):
        return os.path.basename(self.baseline)


def find_test_cases():
    if sys.platform.startswith('win'):
        return
    for script in glob.glob(datadir + '/*.sh'):
        basename = os.path.basename(script)
        name, _ = os.path.splitext(basename)
        for ext in 'txt xml'.split():
            baseline = '{datadir}/{name}.{ext}'.format(
                datadir=datadir, name=name, ext=ext)
            if not os.path.exists(baseline):
                continue
            else:
                yield Example(name, script, baseline)


@pytest.mark.parametrize('example', find_test_cases(), ids=str)
def test_example(example):
    cmd = example.script
    baseline_file = example.baseline
    ext = os.path.splitext(baseline_file)[1][1:]
    scrub = SCRUBBERS[ext]
    assert_equals = ASSERT_EQUALS.get(ext, None)

    startdir = os.getcwd()
    os.chdir(datadir)
    output = scrub(subprocess.check_output(cmd).decode())
    with open(baseline_file) as f:
        baseline = scrub(f.read())
    if assert_equals is not None:
        assert_equals(output, baseline)
    else:
        assert output == baseline
    os.chdir(startdir)
