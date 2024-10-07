.. _coveralls_output:

Coveralls JSON Output
=====================

If you are using Coveralls, you can get a coverage report
in a suitable JSON format via the :option:`--coveralls<gcovr --coveralls>` option::

    gcovr --coveralls coverage.json

The :option:`--coveralls-pretty<gcovr --coveralls-pretty>` option generates
an indented JSON output that is easier to read.

Keep in mind that the output contains the checksums of the source files. If you are
using different OSes, the line endings shall be the same.

If available, environment variable COVERALLS_REPO_TOKEN will be
consumed and baked into the JSON output.

If running in a CI additional variables are used:

- In Travis CI:

  - TRAVIS_JOB_ID
  - TRAVIS_BUILD_NUMBER
  - TRAVIS_PULL_REQUEST
  - TRAVIS_COMMIT
  - TRAVIS_BRANCH

- In Appveyor:

  - APPVEYOR_JOB_ID
  - APPVEYOR_JOB_NUMBER
  - APPVEYOR_PULL_REQUEST_NUMBER
  - APPVEYOR_REPO_COMMIT
  - APPVEYOR_REPO_BRANCH

- In Jenkins CI:

  - JOB_NAME
  - BUILD_ID
  - CHANGE_ID
  - GIT_COMMIT (if available)
  - BRANCH_NAME

- In GitHub Actions:

  - GITHUB_WORKFLOW
  - GITHUB_RUN_ID
  - GITHUB_SHA
  - GITHUB_HEAD_REF (if available)
  - GITHUB_REF

The Coveralls JSON format is documented at
`<https://docs.coveralls.io/api-introduction>`_.

.. versionchanged:: 8.0
   Order of keys changed from alphabetical to logical.

.. versionadded:: 5.0
   Added :option:`--coveralls<gcovr --coveralls>`
   and :option:`--coveralls-pretty<gcovr --coveralls-pretty>`.
