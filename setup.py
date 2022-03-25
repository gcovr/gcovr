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
Script to generate the installer for gcovr.
"""

from runpy import run_path
from setuptools import setup, find_packages
from os import path
import re


version = run_path("./gcovr/version.py")["__version__"]
# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

long_description = re.sub(
    r"^\.\. image:: \./",
    r".. image:: https://raw.githubusercontent.com/gcovr/gcovr/{}/".format(version),
    long_description,
    flags=re.MULTILINE,
)
long_description = re.sub(
    r":option:`(.*?)<gcovr.*?>`", r"``\1``", long_description, flags=re.MULTILINE
)

setup(
    name="gcovr",
    version=version,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    platforms=["any"],
    python_requires=">=3.7",
    packages=find_packages(include=["gcovr*"], exclude=["gcovr.tests"]),
    install_requires=["jinja2", "lxml", "pygments"],
    package_data={
        "gcovr": ["templates/*.css", "templates/*.html"],
    },
    entry_points={
        "console_scripts": [
            "gcovr=gcovr.__main__:main",
        ],
    },
)
