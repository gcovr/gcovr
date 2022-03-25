.. This doesn't yet have the structure of a manpage.
   Achieving that would require changes to how "autoprogram" works.

.. _manpage:

Command Line Reference
======================

The ``gcovr`` command recursively searches a directory tree to find
``gcov`` coverage files, and generates a text summary of the code
coverage.  The :option:`-h/--help<gcovr --help>` option generates the following
summary of the ``gcovr`` command line options:

.. autoprogram:: gcovr.__main__:create_argument_parser()
    :prog: gcovr
    :groups:

For guide-level explanation on using these options,
see the :ref:`guide`.
