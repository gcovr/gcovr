#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________

# Empty gcovr package

from .data import gcov_prefix_split
from .data import is_gcda
from .data import is_gcno
from .data import process_files
from .version import version_str
from .xml_report import print_xml_report
from .text_report import print_text_report
from .html_report import print_html_report
