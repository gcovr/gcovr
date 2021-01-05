# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 4.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2020-2021 Spacetown <michael.foerderer@gmx.de>
# Copyright (c) 2018-2019 Lukas Atkinson <opensource@LukasAtkinson.de>
# Copyright (c) 2018 mayeut <mayeut@users.noreply.github.com>
# Copyright (c) 2013-2016 Hart <whart222@gmail.com>
# Copyright (c) 2013 jsiirola <jsiirola@gmail.com>
# Copyright (c) 2010-2013 wehart <wehart@sandia.gov>
# Copyright (c) 2012 jdsiiro <jdsiiro@sandia.gov>
# and possibly others.
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
from setuptools import setup


version = run_path('./gcovr/version.py')['__version__']

setup(name='gcovr',
      version=version,
      platforms=["any"],
      python_requires='>=3.5',
      packages=['gcovr'],
      install_requires=[
          'jinja2',
          'lxml',
          'pygments'
      ],
      package_data={
          'gcovr': ['templates/*.css', 'templates/*.html'],
      },
      entry_points={
          'console_scripts': [
              'gcovr=gcovr.__main__:main',
          ],
      },
      )
