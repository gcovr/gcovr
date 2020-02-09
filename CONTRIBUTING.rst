Contributing
============

This document contains:

-   our :ref:`guidelines for bug reports <report bugs>`
-   :ref:`general contribution guidelines <help out>`
-   a :ref:`checklist for pull requests <pull request>`
-   a developer guide that explains the
    :ref:`development environment <development environment>`,
    :ref:`project structure <project structure>`,
    and :ref:`test suite <test suite>`

.. _report bugs:

How to report bugs
------------------

When reporting a bug, first `search our issues <search all issues_>`_ to avoid duplicates.
In your bug report, please describe what you expected gcovr to do, and what it actually did.
Also try to include the following details:

-  how you invoked gcovr, i.e. the exact flags and from which directory
-  your project layout
-  your gcovr version
-  your compiler version
-  your operating system
-  and any other relevant details.

Ideally, you can provide a short script
and the smallest possible source file to reproduce the problem.

.. _search all issues: https://github.com/gcovr/gcovr/issues?q=is%3Aissue

.. _help out:

How to help
-----------

If you would like to help out, please take a look at our
`open issues <bugtracker_>`_ and `pull requests`_.
The issues labeled `help wanted <label help wanted_>`_ and
`needs review <label needs review_>`_ would have the greatest impact.

There are many ways how you can help:

-   assist other users with their problems
-   share your perspective as a gcovr user in discussions
-   test proposed changes in your real-world projects
-   improve our documentation
-   submit pull requests with bug fixes and enhancements

.. _bugtracker: https://github.com/gcovr/gcovr/issues
.. _label help wanted: https://github.com/gcovr/gcovr/labels/help%20wanted
.. _label needs review: https://github.com/gcovr/gcovr/labels/needs%20review
.. _pull requests: https://github.com/gcovr/gcovr/pulls

.. _pull request:

How to submit a Pull Request
----------------------------

Thank you for helping with gcovr development!
Please follow this checklist for your pull request:

-   **Is this a good approach?**
    Fixing open issues is always welcome!
    If you want to implement an enhancement,
    please discuss it first as a GitHub issue.

-   **Does it work?**
    Please run the tests locally::

        make test

    (see also: :ref:`test suite`)

    In any case, the tests will run automatically
    when you open the pull request.
    But please prevent unnecessary build failures
    and run the tests yourself first.
    If you cannot run the tests locally,
    you can activate Travis CI or Appveyor for your fork,
    or run the tests with Docker.

    If you add new features, please try to add a test case.

-   **Does it conform to the style guide?**
    The source code should conform to the :pep:`8` standard.
    Please check your code::

        make lint

        # or:

        python3 -m flake8 doc gcovr --ignore E501,W503

    The command ``make qa`` will run the linter, run the tests,
    and check that the docs can be built.

-   **Add yourself as an author.**
    If this is your first contribution to gcovr,
    please add yourself to the ``AUTHORS.txt`` file.

-   **One change at a time.**
    Please keep your commits and your whole pull request fairly small,
    so that the changes are easy to review.
    Each commit should only contain one kind of change,
    e.g. refactoring *or* new functionality.

-   **Why is this change necessary?**
    When you open the PR,
    please explain why we need this change and what your PR does.
    If this PR fixes an open issue,
    reference that issue in the pull request description.

Once you submit the PR, it will be automatically tested on Windows and Linux,
and code coverage will be collected.
Your code will be reviewed.
This can take a week.
Please fix any issues that are discovered during this process.
Feel free to force-push your updates to the pull request branch.

If you need assistance for your pull request, you can

  - chat in `our Gitter room <https://gitter.im/gcovr/gcovr>`_
  - discuss your problem in an issue
  - open an unfinished pull request as a work in progress (WIP),
    and explain what you've like to get reviewed

.. _development environment:

How to set up a development environment
---------------------------------------

For working on gcovr, you will need a supported version of Python 3,
and GCC version 5. Other GCC versions are supported by gcovr,
but will cause spurious test failures.

-   (Optional) Fork the project on GitHub.

-   Clone the git repository.

-   (Optional) Set up a virtualenv (e.g. with ``python3 -m venv my-venv``)

-   Install gcovr in development mode, and install the test requirements::

        make setup-dev  # install all test + doc dependencies

        # or:

        pip install -e .
        pip install -r requirements.txt

    You can then run gcovr as ``gcovr`` or ``python3 -m gcovr``.

    Run the tests to verify that everything works (see :ref:`test suite`).

-   (Optional) Install documentation requirements::

        # would be already done by `make setup-dev`
        pip install -r doc/requirements.txt

    See ``doc/README.txt`` for details on working with the documentation.

-   (Optional) Activate Travis and Appveyor for your forked GitHub repository,
    so that the cross-platform compatibility tests get run
    whenever you push your work to your repository.
    These tests will also be run
    when you open a pull request to the main gcovr repository.

Tip: If you have problems getting everything set up, consider looking at these files:

-   for Linux: ``.travis.yml`` and ``admin/Dockerfile.qa``
-   for Windows: ``appveyor.yml``

On **Windows**, you will need to install a GCC toolchain
as the tests expect a Unix-like environment.
You can use MinGW-W64 or MinGW.
To run the tests,
please make sure that the ``make`` and ``cmake`` from your MinGW distribution
are in the system ``PATH``.

If setting up a local toolchain is too complicated,
you can also run the tests in a Docker container
(see :ref:`test suite`).

.. _project structure:

Project Structure
-----------------

======================= =======================================================
Path                    Description
======================= =======================================================
``/``                   project root
``/gcovr/``             the gcovr source code (Python module)
``/gcovr/__main__.py``  command line interface + top-level behaviour
``/gcovr/templates/``   HTML report templates
``/gcovr/tests/``       unit tests + integration test corpus
``/setup.py``           Python package configuration
``/doc/``               documentation
``/doc/sources/``       user guide + website
``/doc/examples/``      runnable examples for the user guide
======================= =======================================================

The program entrypoint and command line interface is in ``gcovr/__main__.py``.
The coverage data is parsed in the ``gcovr.gcov`` module.
The HTML, XML, text, and summary reports
are in ``gcovr.html_generator`` and respective modules.

.. _test suite:

Test suite
----------

The QA process (``make qa``) consists of multiple parts:

- linting (``make lint``)

- tests (``make test``)

   - unit tests in ``gcovr/tests``
   - integration tests in ``gcovr/tests``
   - documentation examples in ``doc/examples``

- documentation build (``make doc``)

The tests are in the ``gcovr/tests`` directory.
You can run the tests with ``make test`` or ``python3 -m pytest gcovr``.

There are unit tests for some parts of gcovr,
and a comprehensive corpus of example projects
that are executed as the ``test_gcovr.py`` integration test.
Each ``gcovr/tests/*`` directory is one such example project.

The next sections discuss
the :ref:`structure of integration tests <integration tests>`,
how to :ref:`run and filter tests <run tests>`,
and how to :ref:`run tests with Docker <docker tests>`.

.. _integration tests:

Structure of integration tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each project in the corpus
contains a ``Makefile`` and a ``reference`` directory::

   gcovr/tests/sometest/
     reference/
     Makefile
     README
     example.cpp

The Makefile controls how the project is built,
and how gcovr should be invoked.
The reference directory contains baseline files against
which the gcovr output is compared.
Tests can be executed even without baseline files.

Each Makefile contains the following targets:

* ``all:`` builds the example project. Can be shared between gcovr invocations.
* ``run:`` lists available targets
  which must be a subset of the available output formats.
* ``clean:`` remove any generated files
  after all tests of the scenario have finished.
* output formats (txt, html, json, sonarqube, ...):
  invoke gcovr to produce output files of the correct format.
  The test runner automatically finds the generated files (if any)
  and compares them to the baseline files in the reference directory.
  All formats are optional,
  but using at least JSON is recommended.
* ``clean-each:`` if provided, will be invoked by the test runner
  after testing each format.

.. _run tests:

Run and filter tests
~~~~~~~~~~~~~~~~~~~~

To run all tests, use ``make test`` or ``make qa``.
The tests currently assume that you are using GCC 5
and have set up a :ref:`development environment <development environment>`.

Because the tests are a bit slow, you can limit the tests to a specific
test file, example project, or output format.
For example:

.. code:: bash

    # run only XML tests
    python3 -m pytest -k xml

    # run the simple1 tests
    python3 -m pytest -k simple1

    # run the simple1 tests only for XML
    python3 -m pytest -k 'xml and simple1'

    # set filters using the Makefile:
    make test TEST_OPTS="-k 'xml and simple1'"

To see all tests, run pytest in ``-v`` verbose mode.
To see which tests would be run, add the ``--collect-only`` option.

.. _docker tests:

Run tests with Docker
~~~~~~~~~~~~~~~~~~~~~

If you can't set up a toolchain locally, you can run the QA process via Docker.
First, build the container image:

.. code:: bash

    make docker-qa-build

    # or:

    docker build --tag gcovr-qa --file admin/Dockerfile.qa .

Then, run the container, which executes ``make qa`` within the container:

.. code:: bash

    make docker-qa

    # or:

    docker run --rm -v `pwd`:/gcovr gcovr-qa

.. _join:

Become a gcovr developer
------------------------

After you've contributed a bit
(whether with discussions, documentation, or code),
consider becoming a gcovr developer.
As a developer, you can:

-   manage issues and pull requests (label and close them)
-   review pull requests
    (a developer must approve each PR before it can be merged)
-   participate in votes

Just open an issue that you're interested, and we'll have a quick vote.
