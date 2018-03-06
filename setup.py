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

import os
import os.path
import runpy
from setuptools import setup


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames), 'rb').read().decode("UTF-8")


def run_path(filename):
    variables = dict()
    execfile(filename, globals(), variables)  # noqa: F821 execfile()
    return variables


# Retrieve the gcovr version. This prefers to use runpy.run_path() which is
# only supported in Python 2.7 or later, and falls back to execfile() which
# does not exist in Python 3.x.
run_path = getattr(runpy, 'run_path', run_path)
version = run_path('./gcovr/version.py')['__version__']

setup(name='gcovr',
      version=version,
      maintainer='William Hart',
      maintainer_email='wehart@sandia.gov',
      url='http://gcovr.com',
      license='BSD',
      platforms=["any"],
      python_requires='>=2.6',
      description='A Python script for summarizing gcov data.',
      long_description=read('README.rst'),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: BSD License',
          'Natural Language :: English',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Unix Shell',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      packages=['gcovr'],
      install_requires=[
          'argparse ; python_version < "2.7"',
      ],
      keywords=['utility'],
      entry_points={
          'console_scripts': [
              'gcovr=gcovr.__main__:main',
          ],
      },
      )
