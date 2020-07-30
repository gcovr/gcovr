#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
# Copyright 2017 (c) Lei Xu <eddyxu@gmail.com>

import shutil
import tempfile
import unittest

from . import gitrepo


class GitRepoTest(unittest.TestCase):
    def testGitRepoOnNonGitDirectory(self):
        empty_dir = tempfile.mkdtemp()
        try:
            repo = gitrepo.Repository(empty_dir)
            self.assertFalse(repo.valid())
        finally:
            shutil.rmtree(empty_dir, True)
