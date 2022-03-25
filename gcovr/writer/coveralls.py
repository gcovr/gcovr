# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.1, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

from __future__ import absolute_import

import json
import datetime
import functools
import os
import re
import shutil
import subprocess

from hashlib import md5
from ..utils import presentable_filename, open_text_for_writing

PRETTY_JSON_INDENT = 4


def _write_coveralls_result(gcovr_json_dict, output_file, pretty):
    r"""helper utility to output json format dictionary to a file/STDOUT"""
    write_json = json.dump

    if pretty:
        write_json = functools.partial(
            write_json,
            indent=PRETTY_JSON_INDENT,
            separators=(",", ": "),
            sort_keys=True,
        )
    else:
        write_json = functools.partial(write_json, sort_keys=True)

    with open_text_for_writing(output_file, "coveralls.json") as fh:
        write_json(gcovr_json_dict, fh)


def print_coveralls_report(covdata, output_file, options):
    """
    Outputs a JSON report in the Coveralls API coverage format

    @param covdata: is a dictionary of file coverage objects, keyed with an absolute filepath
    @param output_file: is the name of the file to create
    @param options: options object
    """

    # Create object to collect coverage data
    json_dict = {}

    # Capture timestamp
    timestamp: datetime.datetime = options.timestamp.astimezone(datetime.timezone.utc)
    json_dict["run_at"] = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Pull environment variables
    if os.environ.get("COVERALLS_REPO_TOKEN") is not None:
        json_dict["repo_token"] = os.environ.get("COVERALLS_REPO_TOKEN")

    CurrentBranch = None
    CurrentCommit = None
    CurrentPullRequest = None
    # Stub for own test suite
    if os.environ.get("GCOVR_TEST_SUITE") is not None:
        json_dict["service_name"] = "gcovr-test-suite"
        json_dict["service_job_id"] = "id"
        json_dict["service_number"] = "number"
        CurrentPullRequest = "pr"
        CurrentBranch = "branch"
        CurrentCommit = None
    # Consume Travis CI specific environment variables _(if available)_
    # See https://docs.travis-ci.com/user/environment-variables
    elif os.environ.get("TRAVIS_JOB_ID") is not None:
        json_dict["service_name"] = "travis-ci"
        json_dict["service_job_id"] = os.environ.get("TRAVIS_JOB_ID")
        json_dict["service_number"] = os.environ.get("TRAVIS_BUILD_NUMBER")
        CurrentCommit = os.environ.get("TRAVIS_COMMIT")
        CurrentPullRequest = os.environ.get("TRAVIS_PULL_REQUEST")
        CurrentBranch = os.environ.get("TRAVIS_BRANCH")
    # Consume Appveyor specific environment variables _(if available)_
    # See https://www.appveyor.com/docs/environment-variables/
    elif os.environ.get("APPVEYOR_URL") is not None:
        json_dict["service_name"] = "appveyor"
        json_dict["service_job_id"] = os.environ.get("APPVEYOR_JOB_ID")
        json_dict["service_number"] = os.environ.get("APPVEYOR_JOB_NUMBER")
        CurrentCommit = os.environ.get("APPVEYOR_REPO_COMMIT")
        CurrentPullRequest = os.environ.get("APPVEYOR_PULL_REQUEST_NUMBER")
        CurrentBranch = os.environ.get("APPVEYOR_REPO_BRANCH")
    # Consume Jenkins specific environment variables _(if available)_
    # See https://opensource.triology.de/jenkins/pipeline-syntax/globals
    elif os.environ.get("JENKINS_URL") is not None:
        json_dict["service_name"] = "jenkins-ci"
        json_dict["service_job_id"] = os.environ.get("JOB_NAME")
        json_dict["service_number"] = os.environ.get("BUILD_ID")
        if os.environ.get("GIT_COMMIT") is not None:
            CurrentCommit = os.environ.get("GIT_COMMIT")
        CurrentPullRequest = os.environ.get("CHANGE_ID")
        CurrentBranch = os.environ.get("BRANCH_NAME")
    # Consume GitHup Actions specific environment variables _(if available)_
    # See https://docs.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables#default-environment-variables
    elif os.environ.get("GITHUB_ACTIONS") is not None:
        json_dict["service_name"] = "github-actions-ci"
        json_dict["service_job_id"] = os.environ.get("GITHUB_WORKFLOW")
        json_dict["service_number"] = os.environ.get("GITHUB_RUN_ID")
        CurrentCommit = os.environ.get("GITHUB_SHA")
        if os.environ.get("GITHUB_HEAD_REF") is not None:
            CurrentPullRequest = re.sub(
                r"^refs/pull/(\d+)/merge$", r"\1", os.environ.get("GITHUB_HEAD_REF")
            )
            CurrentBranch = os.environ.get("GITHUB_REF")
        else:
            CurrentBranch = re.sub(r"^refs/heads/", "", os.environ.get("GITHUB_REF"))

    if CurrentPullRequest is not None:
        json_dict["service_pull_request"] = CurrentPullRequest

    git = (
        shutil.which("git")
        if os.environ.get("GCOVR_TEST_SUITE_NO_GIT_COMMAND") is None
        else None
    )

    def run_git_cmd(*args):
        process = subprocess.Popen(
            [git] + list(args), stdout=subprocess.PIPE, cwd=options.root_dir
        )
        return process.communicate()[0].decode("UTF-8").rstrip()

    def run_git_log_cmd(arg):
        return run_git_cmd("--no-pager", "log", "-1", "--pretty=format:{}".format(arg))

    if git and "true" in run_git_cmd("rev-parse", "--is-inside-work-tree"):
        if CurrentBranch is None:
            CurrentBranch = run_git_cmd("rev-parse", "--abbrev-ref", "HEAD").rstrip()
        if CurrentCommit is None:
            CurrentCommit = run_git_log_cmd("%H")

        json_dict["git"] = {
            "head": {
                "id": CurrentCommit,
                "author_name": run_git_log_cmd("%aN"),
                "author_email": run_git_log_cmd("%ae"),
                "committer_name": run_git_log_cmd("%cN"),
                "committer_email": run_git_log_cmd("%ce"),
                "message": run_git_log_cmd("%s"),
            },
            "branch": CurrentBranch,
            "remotes": [
                {"name": line.split()[0], "url": line.split()[1]}
                for line in run_git_cmd("remote", "-v").split("\n")
                if line.endswith("(fetch)")
            ],
        }
    elif CurrentCommit is not None:
        json_dict["commit_sha"] = CurrentCommit

    # Loop through each coverage file collecting details
    json_dict["source_files"] = []
    for file_path in sorted(covdata):
        # Object with Coveralls file details
        source_file = {}

        # Generate md5 hash of file contents
        with open(file_path, "rb") as file_handle:
            hasher = md5()
            for data in iter(functools.partial(file_handle.read, 8192), b""):
                hasher.update(data)
            file_hash = hasher.hexdigest()
            source_file["source_digest"] = file_hash

        # Extract FileCoverage object
        coverage_details = covdata[file_path]

        # Isolate relative file path
        relative_file_path = presentable_filename(
            file_path, root_filter=options.root_filter
        )
        source_file["name"] = relative_file_path

        # Initialize coverage array and load with line coverage data
        source_file["coverage"] = []
        # source_file['branches'] = []
        for line in sorted(coverage_details.lines):
            # Extract LineCoverage object
            line_details = coverage_details.lines[line]

            # Comment lines are not collected in `covdata`, but must
            # be reported to coveralls (fill missing lines)
            list_index = len(source_file["coverage"]) + 1
            source_file["coverage"].extend(None for i in range(list_index, line))

            # Skip blank lines _(neither covered or uncovered)_
            if not line_details.is_covered and not line_details.is_uncovered:
                source_file["coverage"].append(None)
                continue

            # Record line counts at corresponding list index
            source_file["coverage"].append(line_details.count)

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
        json_dict["source_files"].append(source_file)

    _write_coveralls_result(json_dict, output_file, options.coveralls_pretty)
