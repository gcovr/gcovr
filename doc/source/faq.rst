.. program:: gcovr

.. _faq:

Frequently Asked Questions
==========================

.. _lcov vs gcovr:

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

.. _lcov website: https://github.com/linux-test-project/lcov
.. _lcov GitHub repository: https://github.com/linux-test-project/lcov


.. _exception branches:

Why does C++ code have so many uncovered branches?
--------------------------------------------------

Gcovr's branch coverage reports are based on GCC's ``-fprofile-arcs`` feature,
which uses the compiler's control flow graph (CFG) of each function
to determine branches.
This is a very low-level view:
to understand the branches in a given function,
it can help to view the function's assembly,
e.g. via the `Godbolt Compiler Explorer`_.

What gcovr calls a *branch* is in fact an *arc* between basic blocks in the CFG.
This means gcovr's reports
have many branches that are not caused by ``if`` statements!
For example:

-   Arcs are caused by C/C++ branching operators:
    ``for``, ``if``, ``while``, ``switch``/``case``,
    ``&&``, ``||``, ``? :``.
    Note that switches are often compiled as a decision tree
    which introduces extra arcs, not just one per case.

-   (Arcs into another function are not shown.)

-   Arcs are caused when a function that may throw returns:
    one arc to the next block or statement for normal returns,
    and one arc to an exception handler for exceptions,
    if this function contains an exception handler.
    Every local variable with a destructor is an exception handler as well.

-   Compiler-generated code that deals with exceptions
    often needs extra branches:
    ``throw`` statements, ``catch`` clauses, and destructors.

-   Extra arcs are created for ``static`` initialization and destruction.

-   Arcs may be added or removed by compiler optimizations.
    If you compile without optimizations, some arcs may even be unreachable!

Gcovr is not able to *remove* any “unwanted” branches
because GCC's gcov tool does not make the necessary information available,
and because different projects are interested in different kinds of branches.
However, gcovr has the following options to *reduce* unwanted branches:

With the :option:`--exclude-unreachable-branches` option,
gcovr parses the *source code* to see whether that line even contains any code.
If the line is empty or only contains curly braces,
this could be an indication of compiler-generated code
that was mis-attributed to that line (such as that for static destruction)
and branch coverage will be ignored on that line.

With the :option:`--exclude-throw-branches` option,
exception-only branches will be ignored.
These are typically arcs from a function call into an exception handler.

Compiling with optimizations will typically remove unreachable branches
and remove superfluous branches,
but makes the coverage report less exact.
For example, branching operators might be optimized away.
Decision coverage analysis will be very buggy when compiling with optimizations.
See also: `Gcov and Optimization`_ in the GCC documentation.

Despite these approaches,
100% branch coverage will be impossible for most programs.

With the :option:`--decisions` option,
gcovr parses the source code to extract a metric for decision coverage.
This metric can be interpreted as the branch coverage on C/C++ level.
While the feature is not always able to detect the decisions reliably
when the code is written very compact (uncheckable decisions will be marked).

Decision coverage may be an acceptable bandaid for C++ code bases, and may be
especially useful for optimistic aggregate metrics (e.g. file-level coverage
percentages and for quality gates using the ``--fail-under-*`` feature). However,
100% "decision" coverage may still leave substantial uncovered control flow.

.. _Godbolt Compiler Explorer: https://godbolt.org/
.. _Gcov and Optimization: https://gcc.gnu.org/onlinedocs/gcc/Gcov-and-Optimization.html

.. _uncovered files not shown:

Why are uncovered files not reported?
-------------------------------------

Gcovr does report files that have zero coverage,
even when no ``.gcda`` file is available for that compilation unit.

However, the gcov tool in some versions of GCC
refuses to generate output for uncovered files.

To fix this, upgrade GCC to:

* version 5.5 or later,
* version 6.2 or later, or
* any version since 7.

Note that the compiler may ignore ``inline`` functions that are never used.


.. _used gcov options:

Which options are used for calling gcov?
----------------------------------------

The options used for calling ``gcov`` depend on the version of gcov.

The following options are always used:

- ``--branch-counts``
- ``--branch-probabilities``
- ``--object-directory``

The following options are only used if available:

- ``--json-format``: Use JSON intermediate format.
- ``--demangled-names``: Not available for LLVM based ``gcov``.
- ``--hash-filenames``: Available since GCC 7, as fallback the option ``--preserve-paths`` is used.
- ``--conditions``: Available since GCC 14, additionally requires the compiler to be invoked with ``-fcondition-coverage``.
