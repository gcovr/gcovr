gcovr
=====

generate GCC code coverage reports

website_ • documentation_ • bugtracker_ • `GitHub <repo_>`_

|travis-ci-badge| |appveyor-ci-badge| |pypi-badge|

.. begin abstract

Gcovr provides a utility for managing the use of the GNU gcov_ utility
and generating summarized code coverage results. This command is
inspired by the Python coverage.py_ package, which provides a similar
utility for Python.

The ``gcovr`` command can produce different kinds of coverage reports:

-  default: compact human-readable summaries
-  ``--xml``: machine readable XML reports in Cobertura_ format
-  ``--html``: HTML summaries
-  ``--html-details``: HTML report with annotated source files

Thus, gcovr can be viewed
as a command-line alternative to the lcov_ utility, which runs gcov
and generates an HTML-formatted report.
The development of gcovr was motivated by the need for
text summaries and XML reports.

.. _gcov: http://gcc.gnu.org/onlinedocs/gcc/Gcov.html
.. _coverage.py: http://nedbatchelder.com/code/coverage/
.. _cobertura: http://cobertura.sourceforge.net/
.. _lcov: http://ltp.sourceforge.net/coverage/lcov.php

.. end abstract

Example HTML summary:

.. image:: ./doc/screenshot-html.png

Example HTML details:

.. image:: ./doc/screenshot-html-details.png

.. _website:        http://gcovr.com/
.. _documentation:  http://gcovr.com/guide.html
.. _repo:       https://github.com/gcovr/gcovr/
.. _bugtracker: https://github.com/gcovr/gcovr/issues
.. |travis-ci-badge| image:: https://travis-ci.org/gcovr/gcovr.svg?branch=master
   :target: https://travis-ci.org/gcovr/gcovr
   :alt: Travis CI build status
.. |appveyor-ci-badge| image:: https://ci.appveyor.com/api/projects/status/6amtekih63rg9f2v/branch/master?svg=true
   :target: https://ci.appveyor.com/project/latk/gcovr-0p8sb/branch/master
   :alt: Appveyor CI build status
.. |pypi-badge| image:: https://img.shields.io/pypi/v/gcovr.svg
   :target: https://pypi.python.org/pypi/gcovr
   :alt: install from PyPI

Installation
------------

.. begin installation

Gcovr is available as a Python package that can be installed via pip_.

.. _pip: https://pip.pypa.io/en/stable

Install newest stable ``gcovr`` release from PyPI:

.. code:: bash

    pip install gcovr

Install development version from GitHub:

.. code:: bash

    pip install git+https://github.com/gcovr/gcovr.git

.. warning::
    Even though gcovr could be used as a single python script file,
    future enhancements will break this capability.
    Instead: always use pip for the installation.

.. end installation

Quickstart
----------

GCC can instrument the executables to emit coverage data.
You need to recompile your code with the following flags:

::

    -fprofile-arcs -ftest-coverage -g -O0

Next, run your test suite.
This will generate raw coverage files.

Finally, invoke gcovr.
This will print a tabular report on the console.

::

    gcovr -r .

You can also generate detailed HTML reports:

::

    gcovr -r . --html --html-details -o coverage.html

Gcovr will create one HTML report per source file next to the coverage.html summary.

You should run gcovr from the build directory.
The ``-r`` option should point to the root of your project.
This only matters if you have a separate build directory.

For complete documentation, read the `manual <documentation_>`_.

Contributing
------------

If you want to report a bug or contribute to gcovr development,
please read our contributing guidelines first:
`<https://github.com/gcovr/gcovr/blob/master/CONTRIBUTING.rst>`_

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
