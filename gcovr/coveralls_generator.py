# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2019 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.
# Filename: coveralls_generator.py
# Author: Zachary J. Fields
# Description: Module to generate Coveralls.io formatted JSON
#              from coverage data collected by `gcovr`
# Modification History:
#

from __future__ import absolute_import

import json
from datetime import datetime
from functools import partial
from .gitrepo.gitrepo import gitrepo
from hashlib import md5
from os import environ
from .utils import presentable_filename


def print_coveralls_report(covdata, output_file, options):
    """
    Outputs a JSON report in the Coveralls API coverage format

    @param covdata: is a dictionary of file coverage objects, keyed with an absolute filepath
    @param output_file: is the name of the file to create
    @param options: options object
    """

    # Create object to collect coverage data
    root = {}

    # Capture timestamp
    root['run_at'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Pull environment variables
    root['repo_token'] = environ.get('COVERALLS_REPO_TOKEN')

    # Consume Travis CI specific environment variables _(if available)_
    root['service_job_id'] = environ.get('TRAVIS_JOB_ID')
    if (root['service_job_id'] is not None):
        root['service_name'] = "travis-ci"
        root['service_number'] = environ.get('TRAVIS_BUILD_NUMBER')
        root['service_pull_request'] = environ.get('TRAVIS_PULL_REQUEST')
    else:
        root['service_name'] = ""
        del root['service_job_id']

    # Add last git commit information
    root['git'] = gitrepo(options.root_dir)

    # Loop through each coverage file collecting details
    root['source_files'] = []
    for file_path in sorted(covdata):
        # Object with Coveralls file details
        source_file = {}

        # Generate md5 hash of file contents
        with open(file_path, 'rb') as file_handle:
            hasher = md5()
            for data in iter(partial(file_handle.read, 8192), b''):
                hasher.update(data)
            file_hash = hasher.hexdigest()
            source_file['source_digest'] = file_hash

        # Extract FileCoverage object
        coverage_details = covdata[file_path]

        # Isolate relative file path
        relative_file_path = presentable_filename(file_path, root_filter=options.root_filter)
        source_file['name'] = relative_file_path

        # Initialize coverage array and load with line coverage data
        source_file['coverage'] = []
        # source_file['branches'] = []
        for line in sorted(coverage_details.lines):
            # Extract LineCoverage object
            line_details = coverage_details.lines[line]

            # Comment lines are not collected in `covdata`, but must
            # be reported to coveralls (fill missing lines)
            list_index = (len(source_file['coverage']) + 1)
            source_file['coverage'].extend(None for i in range(list_index, line))

            # Skip blank lines _(neither covered or uncovered)_
            if not line_details.is_covered and not line_details.is_uncovered:
                source_file['coverage'].append(None)
                continue

            # Record line counts at corresponding list index
            source_file['coverage'].append(line_details.count)

            # Record branch information (INCOMPLETE/OMITTED)
            # branch_details = line_details.branches
            # if branch_details:
            #     b_total, b_hits, coverage = line_details.branch_coverage()
            #     source_file['coverage'].append(line)
            #     # TODO: Add block information to `covdata` object
            #     source_file['coverage'].append(0)
            #     source_file['coverage'].append(b_total)
            #     source_file['coverage'].append(b_hits)

        # File data has been compiled
        root['source_files'].append(source_file)

    # Write to file if specified _(else `stdout`)_
    with open(output_file, 'w') as coveralls_file:
        json.dump(root, coveralls_file)
