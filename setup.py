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

import glob
import os

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

from setuptools import setup
import os.path

if os.path.exists('README.md'):
    import shutil
    shutil.copyfile('README.md', 'README.txt')
scripts = glob.glob("scripts/*")

setup(name='gcovr',
      version='3.3-prerelease',
      maintainer='William Hart',
      maintainer_email='wehart@sandia.gov',
      url = 'http://gcovr.com',
      license = 'BSD',
      platforms = ["any"],
      description = 'A Python script for summarizing gcov data.',
      long_description = read('README.txt'),
      classifiers = [
            'Development Status :: 4 - Beta',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: Unix',
            'Programming Language :: Python',
            'Programming Language :: Unix Shell',
            'Topic :: Software Development :: Libraries :: Python Modules'
        ],
      packages=['gcovr', 'gcovr.prints'],
      keywords=['utility'],
      scripts=scripts
      )

