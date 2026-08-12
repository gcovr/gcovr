# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from gcovr.data_model.coverage import FileCoverage
from gcovr.exclusions import remove_internal_functions


def test_keep_fortran_module_function() -> None:
    """Fortran module procedures are not compiler-generated functions."""
    filecov = FileCoverage("test.gcov", filename="module_help.F90")
    for name in ("__module_help_MOD_help_convert", "__compiler_internal"):
        filecov.insert_function_coverage(
            "test.gcov",
            mangled_name=name,
            demangled_name=None,
            lineno=1,
            count=1,
            blocks=100.0,
        )

    remove_internal_functions(filecov, activate_trace_logging=False)

    assert [functioncov.name for functioncov in filecov.functioncov()] == [
        "__module_help_MOD_help_convert"
    ]


def test_remove_fortran_shaped_function_from_cpp_file() -> None:
    """The Fortran exception must not weaken filtering for other languages."""
    filecov = FileCoverage("test.gcov", filename="module_help.cpp")
    filecov.insert_function_coverage(
        "test.gcov",
        mangled_name="__module_help_MOD_help_convert",
        demangled_name=None,
        lineno=1,
        count=1,
        blocks=100.0,
    )

    remove_internal_functions(filecov, activate_trace_logging=False)

    assert not list(filecov.functioncov())
