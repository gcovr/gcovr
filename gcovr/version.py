# -*- coding:utf-8 -*-
#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________

import re

__version__ = "4.0-prerelease"
src_revision = "$Revision$"


def version_str():
    ans = __version__
    m = re.match('\$Revision:\s*(\S+)\s*\$', src_revision)
    if m:
        ans = ans + " (r%s)" % (m.group(1))
    return ans
