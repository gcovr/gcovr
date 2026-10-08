#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""GCOVR JSON report input."""

import gzip
import json
import os
from glob import glob

from ...data_model import version
from ...data_model.container import CoverageContainer
from ...data_model.merging import (
    FUNCTION_SEPARATE_MERGE_OPTIONS,
    FUNCTION_STRICT_MERGE_OPTIONS,
    get_merge_mode_from_options,
)
from ...filter import is_file_excluded
from ...logging import LOGGER
from ...options import Options
from ...utils import GZIP_SUFFIX


#
#  Get coverage from already existing gcovr JSON files
#
def read_report(options: Options) -> CoverageContainer:
    """Read trace files into internal data model."""
    covdata = CoverageContainer(options.root)
    if len(options.json_tracefile) != 0:
        datafiles = list[str]()

        for trace_file_pattern in options.json_tracefile:
            trace_files = glob(trace_file_pattern, recursive=True)
            if not trace_files:
                msg = (
                    f"Bad --json-add-tracefile={trace_file_pattern} option.\n"
                    "\tThe specified file does not exist."
                )
                raise RuntimeError(msg)

            for trace_file in [
                os.path.normpath(trace_file) for trace_file in trace_files
            ]:
                if trace_file not in datafiles:
                    datafiles.append(trace_file)

        # Here we need to validate the options again because it's possible that one file doesn't exist.
        if options.json_compare and len(datafiles) != 2:  # noqa: PLR2004
            msg = (
                "--json-compare requires exactly two input trace files "
                f"but {len(datafiles)} were given."
            )
            raise RuntimeError(msg)

        merge_options = get_merge_mode_from_options(options)
        if merge_options.func_opts == FUNCTION_STRICT_MERGE_OPTIONS:
            LOGGER.debug("Override merge mode for functions for first tracefile.")
            merge_options.func_opts = FUNCTION_SEPARATE_MERGE_OPTIONS
        for data_source in datafiles:
            activate_trace_logging = not is_file_excluded(
                "trace",
                data_source,
                options.trace_include_filter,
                options.trace_exclude_filter,
            )
            if activate_trace_logging:
                LOGGER.trace("Processing file: %s", data_source)

            if data_source.casefold().endswith(GZIP_SUFFIX):
                with gzip.open(data_source, "rt", encoding="utf-8") as fh:
                    gcovr_json_data = json.loads(fh.read())
            else:
                with open(data_source, encoding="utf-8") as json_file:
                    gcovr_json_data = json.load(json_file)

            format_version = str(gcovr_json_data["gcovr/format_version"])
            if format_version != version.FORMAT_VERSION:
                msg = f"Wrong format version, got {format_version} expected {version.FORMAT_VERSION}."
                raise AssertionError(msg)

            covdata.merge(
                CoverageContainer.deserialize(
                    data_source, gcovr_json_data["files"], options, merge_options
                ),
                merge_options,
            )
            merge_options = get_merge_mode_from_options(
                options, respect_json_compare=True
            )

    return covdata
