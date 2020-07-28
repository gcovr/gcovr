#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________

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
