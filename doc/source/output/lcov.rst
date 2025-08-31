.. program:: gcovr

.. _lcov_output:

LCOV info Output
================

If you are using tools which handle LCOV info file you can get a coverage report
in a suitable info format via the :option:`--lcov` option::

    gcovr --lcov coverage.lcov

If the given name ends with the suffix ``.gz`` the report is compressed by gzip.

With the following options you can set user defined fields in the coverage report:

- :option:`--lcov-comment` defines an optional comment.
- :option:`--lcov-test-name` changes the test name.

Keep in mind that the output contains the checksums of the source files. If you are
using different operating systems, the line endings shall be the same.

The LCOV info format is documented at
`<https://github.com/linux-test-project/lcov/blob/07a1127c2b4390abf4a516e9763fb28a956a9ce4/man/geninfo.1#L989>`_.

.. versionadded:: 7.0
   Added :option:`--lcov`, :option:`--lcov-comment` and :option:`--lcov-test-name`.
