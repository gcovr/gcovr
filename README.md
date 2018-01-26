gcovr
=====

generate GCC code coverage reports

[website] • [documentation] • [bugtracker] • [GitHub][repo]

[![Build Status][travis-ci-badge]][travis-ci] [![Build status][appveyor-ci-badge]][appveyor-ci] [![Install from PyPI][pypi-badge]][pypi]

Gcovr provides a utility for managing the use of the GNU gcov utility
and generating summarized code coverage results. This command is
inspired by the Python coverage.py package, which provides a similar
utility for Python.

The gcovr command can produce different kinds of coverage reports:

  - default: compact human-readable summaries
  - `--xml`: machine readable XML reports in Cobertura format
  - `--html`: HTML summaries
  - `--html-details`: HTML report with annotated source files

Thus, gcovr can be viewed
as a command-line alternative to the lcov utility, which runs gcov
and generates an HTML-formatted report.

Example HTML summary:

![Example HTML summary][fig:html-summary]

Example HTML details:

![Example HTML details][fig:html-details]

  [fig:html-summary]: doc/examples/example1.png
  [fig:html-details]: doc/examples/example2_example1_cpp.png

  [website]:        http://gcovr.com/
  [documentation]:  http://gcovr.com/guide.html
  [repo]:       https://github.com/gcovr/gcovr/
  [bugtracker]: https://github.com/gcovr/gcovr/issues
  [travis-ci]: https://travis-ci.org/gcovr/gcovr
  [travis-ci-badge]: https://travis-ci.org/gcovr/gcovr.svg?branch=master
  [appveyor-ci]: https://ci.appveyor.com/project/latk/gcovr-0p8sb/branch/master
  [appveyor-ci-badge]: https://ci.appveyor.com/api/projects/status/6amtekih63rg9f2v/branch/master?svg=true
  [pypi]: https://pypi.python.org/pypi/gcovr
  [pypi-badge]: https://img.shields.io/pypi/v/gcovr.svg

Installation
------------

Gcovr is available as a Python package that can be installed via [pip].

  [pip]: https://pip.pypa.io/en/stable/

Install newest stable release from PyPI:

    pip install gcovr

Install development version from GitHub:

    pip install git+https://github.com/gcovr/gcovr.git

Quickstart
----------

GCC can instrument the executables to emit coverage data.
You need to recompile your code with the following flags:

    -fprofile-arcs -ftest-coverage -g -O0

Next, run your test suite.
This will generate raw coverage files.

Finally, invoke gcovr.
This will print a tabular report on the console.

    gcovr -r .

You can also generate detailed HTML reports:

    gcovr -r . --html --html-details -o coverage.html

Gcovr will create one HTML report per source file next to the coverage.html summary.

You should run gcovr from the build directory.
The `-r` option should point to the root of your project.
This only matters if you have a separate build directory.

For complete documentation, read the [manual][documentation].

Contributing
------------

When reporting a bug, first [search our issues][search all issues] to avoid duplicates.
In your bug report, please describe what you expected gcovr to do, and what it actually did.
Also try to include the following details:

  - how you invoked gcovr, i.e. the exact flags and from which directory
  - your project layout
  - your gcovr version
  - your compiler version
  - your operating system
  - and any other relevant details.

Ideally, you can provide a short script and the smallest possible source file 
to reproduce the problem.

If you would like to help out, please take a look at our [open issues][bugtracker] and [pull requests].
Maybe you know the answer to some problem,
or can contribute your perspective as a gcovr user.
In particular, testing proposed changes in your real-world project is very valuable.
The issues labeled “[help wanted][label: help wanted]” and “[needs review][label: needs review]” would have the greatest impact.

  [label: help wanted]: https://github.com/gcovr/gcovr/labels/help%20wanted
  [label: needs review]: https://github.com/gcovr/gcovr/labels/needs%20review
  [pull requests]: https://github.com/gcovr/gcovr/pulls
  [search all issues]: https://github.com/gcovr/gcovr/issues?q=is%3Aissue

Pull requests with bugfixes are welcome!
If you want to contribute an enhancement,
please open a new issue first so that your proposal can be discussed and honed.

To work on the gcovr source code, you can clone the git repository, then run “`pip install -e .`”.
To run the tests, you also have to “`pip install pyutilib`”.

Currently, the whole program is in the `scripts/gcovr` file.
It is roughly divided in coverage processing, the various output formats, and in the command line interface.
The tests are in the `gcovr/tests` directory.
You can run the tests with `nosetests -v`.

After you've contributed a bit, consider becoming a gcovr developer.
As a developer, you can:

  - manage issues (label and close them)
  - approve pull requests
  - merge approved pull requests
  - participate in votes

Just open an issue that you're interested, and we'll have a quick vote.

License
-------

Copyright 2013-2018 the gcovr authors

Copyright 2013 Sandia Corporation.
Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
the U.S. Government retains certain rights in this software.

Gcovr is available under the 3-clause BSD License.
See LICENSE.txt for full details.
See AUTHORS.txt for the full list of contributors.

Gcovr development moved to this repository in September, 2013 from
Sandia National Laboratories.

