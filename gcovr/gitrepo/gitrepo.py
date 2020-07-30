"""gitrepo: Module to generate a python JSON object with repository's git details"""

from __future__ import absolute_import
from __future__ import print_function

__author__ = 'Lei Xu <eddyxu@gmail.com>'
__version__ = '0.4.2'

__classifiers__ = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Quality Assurance',
    'Topic :: Utilities',
]

__copyright__ = '2019, %s ' % __author__
__license__ = """
    Copyright %s.
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either expressed or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
    """ % __copyright__

# Filename: gitrepo.py
# Author: Lei "Eddy" Xu
# Copyright: 2019 Lei Xu
# Description: Module to generate a python JSON object with repository's git details
# License: Apache License, Version 2.0
# Modification History:
#

import os
import subprocess


def gitrepo(cwd):
    """Return hash of Git data that can be used to display more information to
    users.

    Example:
        "git": {
            "head": {
                "id": "5e837ce92220be64821128a70f6093f836dd2c05",
                "author_name": "Wil Gieseler",
                "author_email": "wil@example.com",
                "committer_name": "Wil Gieseler",
                "committer_email": "wil@example.com",
                "message": "depend on simplecov >= 0.7"
            },
            "branch": "master",
            "remotes": [{
                "name": "origin",
                "url": "https://github.com/lemurheavy/coveralls-ruby.git"
            }]
        }

    From https://github.com/coagulant/coveralls-python (with MIT license).

    """
    repo = Repository(cwd)
    if not repo.valid():
        return {}

    return {
        'head': {
            'id': repo.gitlog('%H'),
            'author_name': repo.gitlog('%aN'),
            'author_email': repo.gitlog('%ae'),
            'committer_name': repo.gitlog('%cN'),
            'committer_email': repo.gitlog('%ce'),
            'message': repo.gitlog('%s')
        },
        'branch': os.environ.get(
            'TRAVIS_BRANCH',
            os.environ.get(
                'APPVEYOR_REPO_BRANCH',
                repo.git('rev-parse', '--abbrev-ref', 'HEAD')[1].strip()
            )
        ),
        'remotes': [
            {
                'name': line.split()[0],
                'url': line.split()[1]
            }
            for line in repo.git('remote', '-v')[1] if '(fetch)' in line
        ]
    }


class Repository(object):

    def __init__(self, cwd):
        self.cwd = cwd

    def valid(self):
        """
        :return: true if it is a valid git repository.
        """
        return self.git("log", "-1")[0] == 0

    def gitlog(self, fmt):
        return self.git('--no-pager', 'log', '-1', '--pretty=format:%s' % fmt)[1]

    def git(self, *arguments):
        """
        Return (exit code, output) from git.
        """
        process = subprocess.Popen(['git'] + list(arguments),
                                   stdout=subprocess.PIPE,
                                   cwd=self.cwd)
        out = process.communicate()[0].decode('UTF-8')
        code = process.returncode
        return code, out
