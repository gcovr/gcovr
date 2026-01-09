# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.5+main, a parsing and reporting tool for gcov.
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

import os
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec

# ATTENTION: The first environment variable triggers the system in coveralls report
PARAMETERS = [
    (
        "stub",
        {
            "GCOVR_TEST_SUITE": "1",
        },
    ),
    (
        "travis",
        {
            "TRAVIS_JOB_ID": "TRAVIS_JOB_ID",
            "TRAVIS_BUILD_NUMBER": "TRAVIS_BUILD_NUMBER",
            "TRAVIS_PULL_REQUEST": "123",
            "TRAVIS_BRANCH": "test_branch",
            "TRAVIS_COMMIT": "TRAVIS_COMMIT",
        },
    ),
    (
        "appveyor",
        {
            "APPVEYOR_URL": "APPVEYOR_URL",
            "APPVEYOR_JOB_ID": "APPVEYOR_JOB_ID",
            "APPVEYOR_JOB_NUMBER": "APPVEYOR_JOB_NUMBER",
            "APPVEYOR_REPO_COMMIT": "APPVEYOR_REPO_COMMIT",
            "APPVEYOR_PULL_REQUEST_NUMBER": "123",
            "APPVEYOR_REPO_BRANCH": "test_branch",
        },
    ),
    (
        "jenkins",
        {
            "JENKINS_URL": "JENKINS_URL",
            "JOB_NAME": "JOB_NAME",
            "BUILD_ID": "BUILD_ID",
            "GIT_COMMIT": "GIT_COMMIT",
            "CHANGE_ID": "123",
            "BRANCH_NAME": "test_branch",
        },
    ),
    (
        "github_actions",
        {
            "GITHUB_ACTIONS": "GITHUB_ACTIONS",
            "GITHUB_WORKFLOW": "GITHUB_WORKFLOW",
            "GITHUB_RUN_ID": "GITHUB_RUN_ID",
            "GITHUB_SHA": "GITHUB_SHA",
            "GITHUB_REF": "refs/head/test_branch",
        },
    ),
    (
        "github_actions_pr",
        {
            "GITHUB_ACTIONS": "GITHUB_ACTIONS",
            "GITHUB_WORKFLOW": "GITHUB_WORKFLOW",
            "GITHUB_RUN_ID": "GITHUB_RUN_ID",
            "GITHUB_SHA": "GITHUB_SHA",
            "GITHUB_HEAD_REF": "refs/pull/123/merge",
            "GITHUB_REF": "test_branch",
        },
    ),
]


@pytest.mark.parametrize(
    "_test_id,env",
    PARAMETERS,
    ids=[p[0] for p in PARAMETERS],
)
@pytest.mark.coveralls
def test_ci(
    gcovr_test_exec: "GcovrTestExec", _test_id: str, env: dict[str, str]
) -> None:
    """Test for adding CI information to coveralls report."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    new_env = os.environ.copy()
    del new_env["GCOVR_TEST_SUITE"]  # Disable own test suite stub by default
    # Clear all environment variables used for testing
    for env_name in [env_name for p in PARAMETERS for env_name in p[1].keys()]:
        if env_name in new_env:
            del new_env[env_name]
    new_env.update(env)

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--coveralls-pretty",
        "--coveralls=coveralls.json",
        env=new_env,
        use_main=True,
    )
    gcovr_test_exec.compare_coveralls()
