# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

from .json import Json

READERS = [Json()]


class Readers:
    __options_called = False

    @classmethod
    def options(_cls):
        if not _cls.__options_called:
            _cls.__options_called = True
            for r in READERS:
                for o in r.options():
                    yield o

    @classmethod
    def check_options(_cls, options, logger):
        for r in READERS:
            r.check_options(options, logger)

    @classmethod
    def read(_cls, covdata, options, logger):
        for r in READERS:
            r.read(covdata, options, logger)
