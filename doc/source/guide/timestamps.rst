.. program is needed to resolve :option: references
.. program:: gcovr

.. _timestamps:

Reproducible Timestamps
=======================

In some cases, it may be desirable to list a specific timestamp in the report.
Timestamps are shown in
the :ref:`html_output`, :ref:`coveralls_output`, and the :ref:`cobertura_output`.
This can be achieved via the :option:`--timestamp` option
or via :ref:`Using SOURCE_DATE_EPOCH` environment variable.
This option does not affect the modification times or other filesystem metadata.

.. versionadded:: 6.0

   Respect environment variable `SOURCE_DATE_EPOCH`_ for default of :option:`--timestamp`.

.. versionadded:: 5.1

   The :option:`--timestamp` option.


Timestamp Syntax
----------------

The timestamp option understands different formats:
Unix timestamps and RFC-3339 timestamps.

Unix timestamps (also known as Posix time or Epoch)
are the number of seconds since 1 Jan 1970.
These timestamps are always resolved in the UTC timezone.
Example usage:

.. literalinclude:: ../../examples/example_timestamps.sh
   :language: bash
   :start-after: #BEGIN simple epoch
   :end-before: #END simple epoch

:rfc:`3339` specifies a reasonable subset of ISO-8601 timestamps.
This is the ``YYYY-MM-DDThh:mm:ss`` format,
optionally followed by a timezone offset (``+hh:mm``, or ``Z`` for UTC).
Example usage without a timezone:

.. literalinclude:: ../../examples/example_timestamps.sh
   :language: bash
   :start-after: #BEGIN simple RFC 3339
   :end-before: #END simple RFC 3339

Example usages that show equivalent specifications for UTC timestamps:

.. literalinclude:: ../../examples/example_timestamps.sh
   :language: bash
   :start-after: #BEGIN RFC 3339 with UTC timezone
   :end-before: #END RFC 3339 with UTC timezone

Differences and clarifications with respect to RFC-3339:

* the time zone may be omitted
* the date and time parts may be separated by a space character
  instead of the ``T``
* the date is parsed in a case insensitive manner
* sub-second accuracy is not currently supported

Additional formats may be added in the future.
To ensure that timestamps are handled in the expected manner,
it is possible to select a particular timestamp syntax with a prefix.

* Epoch timestamps can be selected with a ``@`` or ``epoch:`` prefix.
* RFC-3339 timestamps can be selected with a ``rfc3339:`` prefix.

Examples of prefixes:

.. literalinclude:: ../../examples/example_timestamps.sh
   :language: bash
   :start-after: #BEGIN prefixes
   :end-before: #END prefixes


Using timestamps from Git commits
---------------------------------

As an example of using the timestamp feature,
we might want to attribute a coverage report
to the time when a Git commit was created.
Git lets us extract the commit date from a commit
with the `git show <https://git-scm.com/docs/git-show>`_ command.
For the current HEAD commit::

  git show --no-patch --format=%cI HEAD

This can be combined into a Bash one-liner like this:

.. literalinclude:: ../../examples/example_timestamps.sh
   :language: bash
   :start-after: #BEGIN git commit
   :end-before: #END git commit

Each Git commit has two dates, the author date and the committer date.
This information can be extracted with various format codes,
e.g. ``%aI`` for the author date and ``%cI`` for the committer date.
These format codes are also available in different formats.
The supported Git formats are:

* Unix timestamps: ``%at``, ``%ct``
* "Strict ISO" format: ``%aI``, ``%cI``
* depending on the ``--date`` option: ``%ad``, ``%cd``

Git's ``--date`` option
is documented in `git log <https://git-scm.com/docs/git-log>`_.
The supported settings are:

* Unix timestamps: ``--date=unix``
* "Strict ISO" format:
  ``--date=iso-strict``,
  ``--date=iso8601-strict``,
  ``--date=iso-strict-local``,
  ``--date=iso8601-strict-local``

.. _Using SOURCE_DATE_EPOCH:

Using SOURCE_DATE_EPOCH
-----------------------

The Reproducible Builds project defines the ``SOURCE_DATE_EPOCH`` variable.
Gcovr will use this variable as a default timestamp
if no explicit :option:`--timestamp` is set.

The contents of this variable *must* be an UTC epoch, without any prefix.
No other format is supported.
Example usage:

.. literalinclude:: ../../examples/example_timestamps.sh
   :language: bash
   :start-after: #BEGIN source date epoch
   :end-before: #END source date epoch

For more information on setting and using this variable,
see the `Reproducible Builds documentation on SOURCE_DATE_EPOCH
<SOURCE_DATE_EPOCH_>`_.

.. _SOURCE_DATE_EPOCH: https://reproducible-builds.org/docs/source-date-epoch/
