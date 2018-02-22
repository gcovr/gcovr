Contributing
============

Reporting bugs
--------------

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

Helping out
-----------

If you would like to help out, please take a look at our `open issues <bugtracker_>`_ and `pull requests`_.
Maybe you know the answer to some problem,
or can contribute your perspective as a gcovr user.
In particular, testing proposed changes in your real-world project is very valuable.
The issues labeled “\ `help wanted <label help wanted_>`_\ ” and “\ `needs review <label needs review_>`_\ ” would have the greatest impact.

.. _bugtracker: https://github.com/gcovr/gcovr/issues
.. _label help wanted: https://github.com/gcovr/gcovr/labels/help%20wanted
.. _label needs review: https://github.com/gcovr/gcovr/labels/needs%20review
.. _pull requests: https://github.com/gcovr/gcovr/pulls

Pull requests with bugfixes are welcome!
If you want to contribute an enhancement,
please open a new issue first so that your proposal can be discussed and honed.

Working with the source code
----------------------------

To work on the gcovr source code, you can clone the git repository,
then run “\ ``pip install -e .``\ ”.
You can then run gcovr as ``gcovr`` or ``python -m gcovr``.

To run the tests, you also have to “\ ``pip install pyutilib pytest flake8``\ ”.

The program entrypoint and command line interface is in ``gcovr/__main__.py``.
The coverage data is parsed in the ``gcovr.gcov`` module.
The HTML, XML, text, and summary reports
are in ``gcovr.html_generator`` and respective modules.

The tests are in the ``gcovr/tests`` directory.
You can run the tests with ``python -m pytest -v``.

The test suite compiles example programs
and compares the gcovr output against baseline files.
This is driven by a Makefile in each ``gcovr/tests/*`` directory.
Because the tests are a bit slow,
you can limit the tests to a specific output format, e.g.:

::

    python -m pytest -v -k GcovrTxt

The output formats are ``Txt``, ``Html``, and ``Xml``.

The tests currently assume that you are using GCC 5.

The source code should conform to the PEP-8 standard,
as checked by the ``flake8`` tool.
You can ignore any existing warnings about E501 (over-long lines).

When you submit a pull request,
your commits will be tested automatically on Windows and Linux.
Please run the tests and the style check locally
to avoid unnecessary build failures.

Become a gcovr developer
------------------------

After you've contributed a bit, consider becoming a gcovr developer.
As a developer, you can:

-  manage issues (label and close them)
-  approve pull requests
-  merge approved pull requests
-  participate in votes

Just open an issue that you're interested, and we'll have a quick vote.
