Frequently Asked Questions
==========================

What is the difference between lcov and gcovr?
----------------------------------------------

Both lcov and gcovr are tools to create coverage reports.

Gcovr was originally created as a simple script
to provide a convenient command line interface to gcov
that produced more easily digestible output
similar to Python's coverage utilities.

Later, we added XML output
that could be used with the Cobertura plugin
of the Jenkins continuous integration server.
This gave us nice coverage reports for C/C++ code in Jenkins.

HTML output was added much later.
If all you need is HTML,
pick whichever one produces the output you like better
or integrates easier with your existing workflow.

Lcov is a far older project that is part of the Linux Test Project.
It provides some features that gcovr does not have:
For example, lcov has explicit support for capturing Linux kernel coverage.
Lcov also supports various trace file manipulation functions
such as merging trace files from different test runs.
You can learn more at the `lcov website`_ or the `lcov GitHub repository`_.

.. _lcov website: http://ltp.sourceforge.net/coverage/lcov.php
.. _lcov GitHub repository: https://github.com/linux-test-project/lcov
