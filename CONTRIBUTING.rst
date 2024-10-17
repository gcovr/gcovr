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

        python3 -m nox

    (see also: :ref:`test suite`)

    In any case, the tests will run automatically
    when you open the pull request.
    But please prevent unnecessary build failures
    and run the tests yourself first.
    If you cannot run the tests locally,
    you can activate GitHub for your fork,
    or run the tests with Docker.
    If there are differences the updated files will be
    available for download from the CI system (one ZIP
    for each test environment).

    If you add new features, please try to add a test case.

-   **Does it conform to the style guide?**
    The source code should conform to the :pep:`8` standard.
    Please check your code::

        python3 -m nox --session lint

    The command ``python3 -m nox`` will run the linters, run the tests,
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
    Add a reference to the issue in the ``CHANGELOG.rst``, if the
    change should not be visible in the changelog (minor or not of
    interest), add the following string to a single line in the PR
    body:

        [no changelog]


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
GCC version 5, 6, 8, 9, 10, 11, 12, 13 or 14 (other GCC versions are
supported by gcovr, but will cause spurious test failures) or clang
version 10, 13, 14 or 15, ``make``, ``cmake``, ``ninja`` and ``bazel``.
Please make sure that the tools are in the system ``PATH``.
On **Windows**, you will need to install a GCC toolchain as the
tests expect a Unix-like environment. You can use MinGW-W64 or MinGW.
An easier way is to :ref:`run tests with Docker <docker tests>`,
on **Windows** a Pro license or the WSL (Windows subsystem for Linux)
is needed.

-   Check your GCC installation, the binary directory must be added to
    the PATH environment. If on of the following command groups are
    everything is OK.

    -  gcc-5/g++-5/gcov-5
    -  gcc-6/g++-6/gcov-6
    -  gcc-8/g++-8/gcov-8
    -  gcc-9/g++-9/gcov-9
    -  gcc-10/g++-10/gcov-10
    -  gcc-11/g++-11/gcov-11
    -  gcc-12/g++-12/gcov-12
    -  gcc-13/g++-13/gcov-13
    -  gcc-14/g++-14/gcov-14
    -  clang-10/clang++-10/llvm-cov
    -  clang-13/clang++-13/llvm-cov
    -  clang-14/clang++-14/llvm-cov
    -  clang-15/clang++-15/llvm-cov
    -  clang-16/clang++-16/llvm-cov

    are available everything is OK.
    The test suite uses the newest GCC found in the PATH. To use another one you
    need to set the environment ``CC=...`` see
    :ref:`run and filter tests <run tests>`.
    If you only have ``gcc`` in your path the version is detected to select the
    correct reference.
    You can also create symlinks for the gcc executables with the following steps.
    You can check the GCC version with gcc --version. If the output says
    version 8, you should also be able to run gcc-8 --version. Your Linux
    distribution should have set all of this up already.
    If you don't have an alias like gcc-8, perform the following steps to
    create an alias for gcc, this should also work in the MSYS shell under Windows:

    1. Create a directory somewhere, e.g. in your home directory: ``mkdir ~/bin``
    2. Create a symlink in that directory which points to GCC: ``ln -s $(which gcc) ~/bin/gcc-8``
    3. Add this directory to your PATH: ``export PATH="$HOME/bin:$PATH"``
    4. Re-test ``gcc-8 --version`` to ensure everything worked.
    5. Create additional symlinks for g++ -> g++-8 and gcov -> gcov-8.


-   (Optional) Fork the project on GitHub.

-   Clone the git repository.

-   (Optional) Set up a virtualenv (e.g. with ``python3 -m venv .venv``)

-   Install gcovr in development mode, and install nox::

        pip install -e .
        pip install nox

    You can then run gcovr as ``gcovr`` or ``python3 -m gcovr``.

    Run the tests to verify that everything works (see :ref:`test suite`).

-   (Optional) Activate GitHub Actions for your forked repository,
    so that the cross-platform compatibility tests get run
    whenever you push your work to your repository.
    These tests will also be run when you open a pull request to the
    main gcovr repository.

Tip: If you have problems getting everything set up, consider looking at these files:

-   for Linux: ``.github/workflows/test.yml`` and ``admin/Dockerfile.qa``
-   for Windows: ``.github/workflows/test.yml``

.. _project structure:

Project Structure
-----------------

======================= =======================================================
Path                    Description
======================= =======================================================
``/``                   project root
``/gcovr/``             the gcovr source code (Python module)
``/gcovr/__main__.py``  command line interface + top-level behavior
``/gcovr/templates/``   HTML report templates
``/tests/``             unit tests + integration test corpus
``/noxfile.py``         Definition of tests tasks
``/setup.py``           Python package configuration
``/doc/``               documentation
``/doc/sources/``       user guide + website
``/doc/examples/``      runnable examples for the user guide
======================= =======================================================

The program entrypoint and command line interface is in ``gcovr/__main__.py``.
The coverage data is parsed in the ``gcovr.formats.gcov`` module.
The HTML, XML, text, and summary reports
are in ``gcovr.formats.html`` and respective modules.

.. _test suite:

Test suite
----------

The QA process (``python3 -m nox``) consists of multiple parts:

- linting and checking format(``python3 -m nox --session lint``)

- tests (``python3 -m nox --session tests``)

   - unit tests in ``tests``
   - integration tests in ``tests``
   - documentation examples in ``doc/examples``

- documentation build (``python3 -m nox --session doc``)

The tests are in the ``tests`` directory.
You can run the tests with ``python3 -m nox --session tests``
for the default GCC version (specified via ``CC`` environment variable, defaults to gcc-5).


There are unit tests for some parts of gcovr,
and a comprehensive corpus of example projects
that are executed as the ``test_gcovr.py`` integration test.
Each ``tests/*`` directory is one such example project.

You can format files with ``python3 -m nox --session black``)

To get a list of all available sessions run ``python3 -m nox -l``.

The next sections discuss
the :ref:`structure of integration tests <integration tests>`,
how to :ref:`run and filter tests <run tests>`,
and how to :ref:`run tests with Docker <docker tests>`.

.. versionchanged:: 5.2
   If black is called without arguments, all files are reformated
   instead of checked. To check the format use the session lint.

.. _integration tests:

Structure of integration tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each project in the corpus
contains a ``Makefile`` and a ``reference`` directory::

   tests/some-test/
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

To run all tests, use ``python3 -m nox``.
The tests currently assume that you are using GCC 5
and have set up a :ref:`development environment <development environment>`.
You can select a different GCC version by setting the CC environment variable.
Supported versions are ``CC=gcc-5``, ``CC=gcc-6``, ``CC=gcc-8``, ``CC=gcc-9``,
``gcc-10``, ``gcc-11``, ``gcc-12``, ``gcc-13``, ``gcc-14``, ``clang-10``,
``clang-13``, ``clang-14`` and ``clang-15``.

You can run the tests with additional options by adding ``--`` and then the options
to the test invocation. Run all tests after each change is a bit slow, therefore you can
limit the tests to a specific test file, example project, or output format.
For example:

.. code:: bash

    # run only XML tests
    python3 -m nox --session tests -- -k 'xml'

    # run the simple1 tests
    python3 -m nox --session tests -- -k 'simple1'

    # run the simple1 tests only for XML
    python3 -m nox --session tests -- -k 'xml and simple1'

To see which tests would be run, add the ``--collect-only`` option:

.. code:: bash

    #see which tests would be run
    python3 -m nox --session tests -- --collect-only

Sometimes during development you need to create reference files for new test
or update the current reference files. To do this you have to
add ``--generate_reference`` or ``--update_reference`` option
to the test invocation.
By default generated output files are automatically removed after test run.
To skip this process you can add ``--skip_clean`` option the test invocation.
For example:

.. code:: bash

    # run tests and generate references for simple1 example
    python3 -m nox --session tests -- -k 'simple1' --generate_reference

    # run tests and update xml references for simple1 example
    python3 -m nox --session tests -- -k 'xml and simple1' --update_reference

    # run only XML tests and do not remove generated files
    python3 -m nox --session tests -- -k 'xml' --skip_clean

To update the reference data for all compiler in one call see
:ref:`run tests with Docker <docker tests>`.

When the currently generated output reports differ to the reference files
you can create a ZIP archive named ``diff.zip`` in the tests directory
by using ``--archive_differences`` option.
Currently in gcovr it is used by GitHub CI to create a ZIP file
with the differences as an artifact.

.. code:: bash

    # run tests and generate a ZIP archive when there were differences
    python3 -m nox --session tests -- --archive_differences

.. versionchanged:: 5.1
    Change how to start test from ``make test`` to ``python3 -m nox --session tests``

.. versionadded:: 5.0
   Added test options `--generate_reference`, `--update_reference`,
   `--skip_clean`, '--archive_differences' and changed way to call tests
   only by ``make test``.

.. _docker tests:

Run tests with Docker
~~~~~~~~~~~~~~~~~~~~~

If you can't set up a toolchain locally, you can run the QA process via Docker.
First, build the container image:

.. code:: bash

    python3 -m nox --session docker_build

Then, run the container, which executes ``nox`` within the container:

.. code:: bash

    python3 -m nox --session docker_run -s qa

Or to build and run the container in one step:

.. code:: bash

    python3 -m nox --session docker_qa

You can select the gcc version to use inside the docker by setting the environment
variable CC to gcc-5 (default), gcc-6, gcc-8, gcc-9, gcc-10, gcc-11, gcc-12,
gcc-13, gcc-14, clang-10, clang-13, or clang-14 or you can build and run the container with:

.. code:: bash

    python3 -m nox --session 'docker_compiler(gcc-9)'

To run a specific session you can use the session ``docker_compiler``
and give the arguments to the ``nox`` executed inside the container
after a ``--`` :

.. code:: bash

    python3 -m nox --session 'docker_compiler(gcc-9)' -- -s tests

You can also use the compiler 'all' to run the tests for all compiler versions,
'gcc' to only use the ``gcc`` versions, or 'clang' to use ``clang`` versions.
A useful command to update all the reference files is :

.. code:: bash

    python3 -m nox --session 'docker_compiler(all)' -- -s tests -- --update_reference

.. _devcontainer:

Use a devcontainer
~~~~~~~~~~~~~~~~~~

For developing ``gcovr`` you can use whatever editor you want.
If the editor supports Devcontainers (e.g. VS Code) you do not
need to install the needed tools on your local system.
You can also use ``GitHub Codespaces`` to contribute to the project.

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
