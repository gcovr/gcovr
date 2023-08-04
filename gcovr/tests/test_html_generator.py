# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import logging
import os
import sys

import pytest

from ..formats.html.write import _make_short_sourcename

CurrentDrive = os.getcwd()[0:1]


@pytest.mark.parametrize(
    "outfile,source_filename",
    [
        ("../gcovr", "C:\\other_dir\\project\\source.c"),
        ("../gcovr/", "C:\\other_dir\\project\\source.c"),
        ("..\\gcovr", "C:\\other_dir\\project\\source.c"),
        ("..\\gcovr\\", "C:\\other_dir\\project\\source.c"),
        (
            "..\\gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        ("..\\gcovr\\result.html", "C:\\other_dir\\project\\source.c"),
        (
            "..\\gcovr\\result",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:\\gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:/gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:/gcovr_files",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
    ],
)
@pytest.mark.skipif(sys.platform != "win32", reason="only for Windows")
def test_windows__make_short_sourcename(outfile, source_filename):
    outfile = outfile.replace("C:", CurrentDrive)
    source_filename = source_filename.replace("C:", CurrentDrive)

    result = _make_short_sourcename(outfile, source_filename)
    logging.info("=" * 100)
    logging.info(outfile)
    logging.info(source_filename)
    logging.info(result)
    assert ":" not in result or (
        result.startswith(CurrentDrive) and ":" not in result[2:]
    )

    assert len(result) < 256


@pytest.fixture(scope="session")
def template_dir(tmp_path_factory):
    """
    Return alternate template directory where base.html and directory_page.summary.html
    are replaced
    """
    # Build temp directory and filenames
    template_dir: pathlib.Path = tmp_path_factory.mktemp("alt_templates", numbered=True)
    base_template = template_dir / "base.html"
    directory_template = template_dir / "directory_page.summary.html"

    # Write some content we can spot in the templates
    base_template.write_text("NEW_BASE_TEMPLATE")
    directory_template.write_text("NEW_DIRECTORY_TEMPLATE")

    return template_dir


def test_template_dir_fallthrough(template_dir):
    from gcovr.formats.html.write import templates

    # Inject options to set --html-template-dir to temporary directory
    # created in fixture
    class TestTemplateDir(object):
        html_template_dir = template_dir

    tdir = TestTemplateDir()

    env = templates(tdir)

    # Ensure our two overriden templates come from this temporary directory
    base = env.get_template("base.html")
    directory_template = env.get_template("directory_page.summary.html")

    # Test non-overriden template
    functions_template = env.get_template("functions_page.html")

    assert str(template_dir) in base.filename
    assert str(template_dir) in directory_template.filename
    assert str(template_dir) not in functions_template.filename
