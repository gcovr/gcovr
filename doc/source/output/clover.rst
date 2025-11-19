.. program:: gcovr

.. _clover_output:

Clover XML Output
=================

The ``gcovr`` command can generate a
Clover XML output using the :option:`--clover`
and :option:`--clover-pretty` options:

.. literalinclude:: ../../examples/example_clover.sh
    :language: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an XML summary of the lines executed:

.. literalinclude:: ../../examples/example_clover.xml
    :language: xml

This XML format is described in the
`Clover XML <https://bitbucket.org/atlassian/clover/src/master/etc/schema/clover.xsd>`__
XSD suitable for import and display within the
`Atlassian Bamboo <https://www.atlassian.com/de/software/bamboo>`__
continuous integration servers.

The :option:`--clover` option generates a denser XML output, and the
:option:`--clover-pretty` option generates an indented
XML output that is easier to read.

If the given name ends with the suffix ``.gz`` the report is compressed by gzip,
if it ends with ``.xz`` it is compressed by LZMA.

.. versionadded:: 7.1

    Add :option:`--clover` and :option:`--clover-pretty`.
