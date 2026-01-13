
.. program::  gcovr

.. _known_bugs:

Known bugs
==========

This list contains bugs for version 6.0 and newer, always check the latest
version of this file available `here <https://gcovr.com/en/latest/known_bugs.html>`_.

.. _fix_1231:

Merge assertion error for functions defined in multiple lines
-------------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_5`

   * - Fixed
     - :ref:`release_8_6`, :issue:`1231`

The lin number of the first source line which is hit is used for the function
definition. Correct is the first source line independent from the content.
This was the behavior before :issue:`1204`.

.. _fix_1229:

Merge assertion error for function ``<unknown function>``
---------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_5`

   * - Fixed
     - :ref:`release_8_6`, :issue:`1229`

Always add the line numbers for the ``unknown function`` added with :issue:`1204` because the lines
can be different for different compilation units. E.g.:

.. code-block::

  gcovr.exceptions.GcovrMergeAssertionError: <file>:<line> Got function <unknown function> on multiple lines: 123, 456.
    You can run gcovr with --merge-mode-functions=MERGE_MODE.
    The available values for MERGE_MODE are described in the documentation.

With the fix we will have two functions in the report:

- Function: ``<unknown function 123>``
- Function: ``<unknown function 456>``

.. _fix_1206_1:

Fix excluded functions in HTML report
-------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1206`

The excluded functions where marked as ``not called`` instead of ``excluded`` in
the HTML report.

.. _fix_1206_2:

Fix LCOV report if function is defined in multiple lines
--------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1206`

The created postfix for ``FNDA`` entry always contains the last line of the function.

.. code-block::
  :caption: Snippet of LCOV report

  FN:3,foo(int)_3
  FN:5,foo(int)_5
  FNDA:1,foo(int)_5
  FNDA:1,foo(int)_5

.. _fix_1197:

Nested HTML report without data can't be generated
--------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_6_0`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1197`

When generating a nested HTML report but there is no coverage data
for :ref:`release_6_0` to :ref:`release_8_2` no root page is generated
and no error is raised. Starting with :ref:`release_8_3` the following error occurs:

.. code-block::

  (ERROR) Error occurred while printing reports:
  Traceback (most recent call last):
    File "/gcovr/src/gcovr/__main__.py", line 426, in main
      gcovr_formats.write_reports(covdata, options)
    File "/gcovr/src/gcovr/formats/__init__.py", line 311, in write_reports
      format_writer(covdata, output.abspath)
    File "/gcovr/src/gcovr/formats/html/__init__.py", line 282, in write_report
      write_report(covdata, output_file, self.options)
    File "/gcovr/src/gcovr/formats/html/write.py", line 484, in write_report
      write_directory_pages(
    File "/gcovr/src/gcovr/formats/html/write.py", line 610, in write_directory_pages
      root_key = next(iter(sorted([d.dirname for d in covdata.directories])))
  StopIteration

.. _fix_1194_1:

Drastic increase of runtime with large projects
-----------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1194`

The runtime of ``gcovr`` increased drastically if a project had source files with many lines and functions.

- In :issue:`1193` the runtime increased from 1,3s to 350s for a file with data for
  ~5.000 functions, ~75.000 lines of code with ~95.000 branches and ~60.000 calls.
- In :issue:`1164` the runtime increased from ~43s to ~150s for the provided data.

.. _fix_1194_2:

Data source in JSON report can contain wrong information
--------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1194`

The set used to store the data source is shared for all items of the
input file. Merging data from another source e.g. for a line is adding
the data source to all other locations.

.. _fix_1192:

`TypeError` in text report for covered decisions
------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1192`

If text report for covered decisions is created with :option:`--txt-report-covered` and
:option:`--txt-metric=decision` following error occurs:

.. code-block::

  (ERROR) Error occurred while printing reports:
  Traceback (most recent call last):
    File "/gcovr/src/gcovr/__main__.py", line 426, in main
      gcovr_formats.write_reports(covdata, options)
    File "/gcovr/src/gcovr/formats/__init__.py", line 311, in write_reports
      format_writer(covdata, output.abspath)
    File "/gcovr/src/gcovr/formats/txt/__init__.py", line 105, in write_report
      write_report(covdata, output_file, self.options)
    File "/gcovr/src/gcovr/formats/txt/write.py", line 82, in write_report
      (stat, txt) = _summarize_file_coverage(covdata[key], options)
    File "/gcovr/src/gcovr/formats/txt/write.py", line 130, in _summarize_file_coverage
      covered_lines = _covered_decisions_str(filecov)
    File "/gcovr/src/gcovr/formats/txt/write.py", line 223, in _covered_decisions_str
      covered_decisions = sorted(
  TypeError: 'method' object is not iterable

.. _fix_1189:

Line coverage missing if template functions are used
----------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1189`

With release :ref:`release_8_4` we ignored lines without a function name.
If template functions are used there are separators in ``gcov`` text format
before and after the function specialization. The lines after the specialization
were ignored because the function name was set to ``None``.

.. code-block::
  :caption: Snippet of ``gcov`` file provided in :issue:`1168`

          -:  844:    const std::unordered_map<Kind, std::function<catena::exception_with_status(const st2138::Value&, Path::Index, const IAuthorizer&)>> validateSetValueMap_ {
         45:  845:        {Kind::kInt32Value, [this](const st2138::Value& protoVal, Path::Index index, const IAuthorizer& authz) {
  call    0 returned 2
  call    1 returned 15
  call    2 returned 1
  call    3 returned 1
  call    4 returned 16
  ------------------
  catena::common::ParamWithValue<int>::validateSetValueMap_::{lambda(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&)#1}::operator()(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&) const:
  function catena::common::ParamWithValue<int>::validateSetValueMap_::{lambda(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&)#1}::operator()(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&) const called 3 returned 100% blocks executed 100%
          3:  845:        {Kind::kInt32Value, [this](const st2138::Value& protoVal, Path::Index index, const IAuthorizer& authz) {
  ------------------
  catena::common::ParamWithValue<std::vector<int, std::allocator<int> > >::validateSetValueMap_::{lambda(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&)#1}::operator()(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&) const:
  function catena::common::ParamWithValue<std::vector<int, std::allocator<int> > >::validateSetValueMap_::{lambda(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&)#1}::operator()(st2138::Value const&, unsigned long, catena::common::IAuthorizer const&) const called 7 returned 100% blocks executed 100%
          7:  845:        {Kind::kInt32Value, [this](const st2138::Value& protoVal, Path::Index index, const IAuthorizer& authz) {
  ------------------
         20:  846:            return this->validateSetValue_(this->get(), protoVal.int32_value(), protoVal, index, authz);
          3:  846-block  0
  call    0 returned 3
  branch  1 taken 3 (fallthrough)
  branch  2 taken 0 (throw)
          3:  846-block  1
  call    3 returned 3
  call    4 returned 3
  branch  5 taken 3 (fallthrough)
  branch  6 taken 0 (throw)
          3:  846-block  2
          3:  846-block  3
          7:  846-block  4
  call    7 returned 7
  branch  8 taken 7 (fallthrough)
  branch  9 taken 0 (throw)
          7:  846-block  5
  call   10 returned 7
  call   11 returned 7
  branch 12 taken 7 (fallthrough)
  branch 13 taken 0 (throw)
          7:  846-block  6
          7:  846-block  7
          -:  847:        }},

.. _fix_1187:

Detection of version mismatch between gcc and gcov doesn't work
---------------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1187`

The regular version for detecting version mismatch between ``gcc`` and ``gcov``
didn't match the following strings:

- ``...:version '...', prefer '...'``
- ``...:version '...', prefer version '...'``

.. _fix_1176:

Exclusion filter for existing GCOV files doesn't work
-----------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_3`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1176`

The exclusion filter given by :option:`--gcov-exclude` isn't applied.
The message ``Excluding gcov file: ...`` is printed but the file is still used.

.. _fix_1171_1:

Branch exclusion comments remove the branches complete and do not affect conditions
-----------------------------------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_0`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1171`

If a line is excluded by comments and contains branches and conditions, the branches and
conditions are excluded and the decisions are cleared.
If branches are excluded by comments they are removed completely but the conditions
are still reported.
With the fix the branch exclusion comments exclude both the branches and conditions
and clear the decisions as if the line was excluded.

.. _fix_1171_2:

Excluded branches ar still reported in LCOV report
--------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1171`

When a line with branches is excluded the branch exclusion flag is
ignored and there are still ``BRDA`` lines created in the ``LCOV`` report.

.. _fix_1165:

Multiple counters for same line are not merged in coveralls report
------------------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_4`

   * - Fixed
     - :ref:`release_8_5`, :issue:`1165`

Since version 8.4 there can be several coverage elements for same line. This data
isn't merged in coveralls report. The elements are added as several elements to the
``coverage`` list in the coveralls report which result in wrong data for the
following lines.

.. _fix_1138:

Wrong data used in clover report
--------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_7_1`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1138`

- ``loc`` contains the highest line number with coverage information instead of lines of the file.
- ``ncloc`` contains the number of reportable lines instead of the lines of the file without comments.
- ``statements`` and ``coveredstatements`` are always set to zero but lines of type ``stmt`` are added
  to the report.

.. _fix_1137:

Discrepancy between exclusion and removal of coverage data
----------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_0`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1137`

- The internal functions where removed but the line coverage was only excluded. Now the line
  coverage data is also removed.
- The coverage of a whole line was removed if a function started on this line, even if the line
  coverage belongs to another function. Now only the data for this function is removed.

.. _fix_1130:

Files without functions and lines are added to report
-----------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_0`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1130`

Files without functions and lines from ``gcov`` JSON report are added to data model.

.. code-block:: json
  :caption: Snippet from ``gcov`` JSON report

  {
    "file": "/path/to/file.h",
    "functions": [],
    "lines": []
  }

.. _fix_1126:

Wrong handling of functions with specialization
-----------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_3`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1126`

- With gcc-5, gcc-6 and clang compiler functions with specializations
  (template functions) use one block in the output which starts with all
  names. All functions are added to the data model but only the last one
  has coverage data (of all functions). A debug message is printed for
  each function which will not contain any line coverage.

  **This can't be changed on our side because of missing information.**

.. code-block::
  :caption: Template specialization for gcc-5, gcc-6 and clang

  function foo() called 1 returned 100% blocks executed 100%
          1:    3:void foo() {
          1:    3-block  0
          1:    4:   std::cout << "Hello from foo()." << std::endl;
          1:    4-block  0
  call    0 returned 1
  call    1 returned 1
          1:    5:}
          -:    6:
          -:    7:template<typename T>
  function void func<double>(double, double) called 2 returned 100% blocks executed 33%
  function void func<int>(int, int) called 2 returned 100% blocks executed 100%
          4:    8:void func(T a, T b) {
          2:    8-block  0
          2:    8-block  1
          4:    9:   if (a < b) {
          2:    9-block  0
  branch  0 taken 0 (fallthrough)
  branch  1 taken 2
          2:    9-block  1
  branch  2 taken 1 (fallthrough)
  branch  3 taken 1
          1:   10:      std::cout << a << " is less than " << b << std::endl;
      $$$$$:   10-block  0
  call    0 never executed
  call    1 never executed
  call    2 never executed
  call    3 never executed
          1:   10-block  1
  call    4 returned 1
  call    5 returned 1
  call    6 returned 1
  call    7 returned 1
          -:   11:   }
          4:   12:}

- For gcc-8 and newer (unless GCOV JSON is used) the output of functions
  with specialization starts with a block with overall coverage followed
  by a block for each specialized function. If a normal function was in
  front of this block the overall counts where added to this function.

  This data is now removed again after detecting the specialization and a
  debug message is printed.

.. code-block::
  :caption: Template specialization for gcc-8 and newer

          -:    2:
  function foo() called 1 returned 100% blocks executed 100%
          1:    3:void foo() {
          1:    4:   std::cout << "Hello from foo()." << std::endl;
          1:    4-block  0
  call    0 returned 1
  call    1 returned 1
          1:    5:}
          -:    6:
          -:    7:template<typename T>
          4:    8:void func(T a, T b) {
          4:    9:   if (a < b) {
        1*:   10:      std::cout << a << " is less than " << b << std::endl;
          -:   11:   }
          4:   12:}
  ------------------
  void func<double>(double, double):
  function void func<double>(double, double) called 2 returned 100% blocks executed 33%
          2:    8:void func(T a, T b) {
          2:    9:   if (a < b) {
          2:    9-block  0
  branch  0 taken 0 (fallthrough)
  branch  1 taken 2
      #####:   10:      std::cout << a << " is less than " << b << std::endl;
      %%%%%:   10-block  0
  call    0 never executed
  call    1 never executed
  call    2 never executed
  call    3 never executed
          -:   11:   }
          2:   12:}
  ------------------
  void func<int>(int, int):
  function void func<int>(int, int) called 2 returned 100% blocks executed 100%
          2:    8:void func(T a, T b) {
          2:    9:   if (a < b) {
          2:    9-block  0
  branch  0 taken 1 (fallthrough)
  branch  1 taken 1
          1:   10:      std::cout << a << " is less than " << b << std::endl;
          1:   10-block  0
  call    0 returned 1
  call    1 returned 1
  call    2 returned 1
  call    3 returned 1
          -:   11:   }
          2:   12:}
  ------------------

- A forced inline function does not contain a function name in the
  output. If the function is at the begin of the output it is ignored
  and a debug message is printed.
  In the middle of the file it is still added to the previous function.

  **This can’t be changed on our side because of missing information.**

.. code-block::
  :caption: Forced inline function at file start (ignored by fix)

          -:    0:Source:main.cpp
          -:    0:Graph:./testcase-main.gcno
          -:    0:Data:./testcase-main.gcda
          -:    0:Runs:1
          -:    1:
          -:    2:inline int foo(int x) __attribute__((always_inline));
          -:    3:inline int foo(int x) {
        1*:    4:  return x ? 1 : 0;
      %%%%%:    4-block  0
          1:    4-block  1
          1:    4-block  2
          1:    4-block  3
          -:    5:}
          -:    6:
  function main called 1 returned 100% blocks executed 86%
          1:    7:int main() {
          1:    7-block  0
  branch  0 taken 0 (fallthrough)
  branch  1 taken 1
          1:    8:    return foo(0);
          1:    8-block  0
          -:    9:}

.. _fix_1092:

Error if conditions for the same line are reported different across GCOV data files
-----------------------------------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_3`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1092`

The number and the order of the items reported by ``GCOV`` can differ between the compilation
units or between the runs. With the fix the data is merged if they have the same properties
instead of the position in the list which failed because of the different properties.
The properties taken into account are described in :ref:`json_output`

E.g. from a project ``GCOV`` reported following data for a line defined in a header.

.. code-block:: json
  :caption: file.gcov from file_a.gcda

  {
      "line_number": 970,
      "count": 0,
      "unexecuted_block": true,
      "block_ids": [
          3
      ],
      "branches": [
          {
              "count": 0,
              "throw": false,
              "fallthrough": true,
              "source_block_id": 3,
              "destination_block_id": 4
          },
          {
              "count": 0,
              "throw": false,
              "fallthrough": false,
              "source_block_id": 3,
              "destination_block_id": 5
          }
      ],
      "calls": [],
      "conditions": [
          {
              "count": 2,
              "covered": 0,
              "not_covered_true": [
                  0
              ],
              "not_covered_false": [
                  0
              ]
          }
      ]
  }

.. code-block:: json
  :caption: file.gcov from file_b.gcda

  {
      "line_number": 970,
      "count": 593,
      "unexecuted_block": true,
      "block_ids": [
          6,
          3
      ],
      "branches": [
          {
              "count": 0,
              "throw": false,
              "fallthrough": true,
              "source_block_id": 6,
              "destination_block_id": 7
          },
          {
              "count": 0,
              "throw": false,
              "fallthrough": false,
              "source_block_id": 6,
              "destination_block_id": 8
          },
          {
              "count": 0,
              "throw": false,
              "fallthrough": true,
              "source_block_id": 3,
              "destination_block_id": 4
          },
          {
              "count": 593,
              "throw": false,
              "fallthrough": false,
              "source_block_id": 3,
              "destination_block_id": 5
          }
      ],
      "calls": [],
      "conditions": [
          {
              "count": 4,
              "covered": 0,
              "not_covered_true": [
                  0,
                  1
              ],
              "not_covered_false": [
                  0,
                  1
              ]
          },
          {
              "count": 2,
              "covered": 1,
              "not_covered_true": [],
              "not_covered_false": [
                  0
              ]
          }
      ]
  }

.. _fix_1089:

JaCoCo report does not follow the DTD schema
--------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_7_0`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1089`

``JaCoCo`` report does not follow the DTD.

.. _fix_1085:

Multiple functions with same name in Cobertura report
-----------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_3`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1085`

``Cobertura`` report contains multiple functions with same name for virtual destructors and const overloads.

.. _fix_1080:

Missing excluded property for condition in JSON report
------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_3`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1080`

``JSON`` report doesn't contain ``excluded`` property for conditions and calls.

.. _fix_1066:

Wrong log message: Deprecated config key None used, please use ...
------------------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_3`

   * - Fixed
     - :ref:`release_8_4`, :issue:`1066`

The log message ``Deprecated config key None used, please use 'txt-metric=branch' instead.`` is printed
even if the mentioned key is used.

.. _fix_1048:

Negative counters in GCOV JSON intermediate file are not handled
----------------------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_0`

   * - Fixed
     - :ref:`release_8_3`, :issue:`1048`

Because of a bug in GCOV (see `<https://gcc.gnu.org/bugzilla/show_bug.cgi?id=68080>`_)
we can get negative counter values in the GCOV reports.
The handling of this negative counters was missing is missing if we use JSON
intermediate file.

.. _fix_1037:

Wrong source root in Cobertura report
-------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_6_0`

   * - Fixed
     - :ref:`release_8_3`, :issue:`1037`

For the source root path in ``Cobertura`` report a relative path is used
instead of an absolute one. When reading the report the root was ignored.

.. _fix_1022:

Overall summary in JaCoCo report is wrong
-----------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_7_0`

   * - Fixed
     - :ref:`release_8_3`, :issue:`1022`

The overall summary stats in ``JaCoCo`` report contains the stats ot the
last file in the report.

.. _fix_1012:

Excluded lines are added to LCOV report
---------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_2`

   * - Fixed
     - :ref:`release_8_3`, :issue:`1012`

The excluded lines are added with a count of 0 to the ``LCOV`` report.

.. _fix_987:

Exclusion of internal function raises a KeyError
------------------------------------------------

.. list-table::

   * - Introduced
     - :ref:`release_8_0`

   * - Fixed
     - :ref:`release_8_1`, :issue:`987`

If internal functions are excluded ``GCOVR`` fails with a stack backtrace:

.. code-block::

  (INFO) Reading coverage data...

  Traceback (most recent call last):
    File "gcovr/formats/gcov/workers.py", line 81, in worker
      work(*args, **kwargs)
    File "gcovr/formats/gcov/read.py", line 566, in process_datafile
      done = run_gcov_and_process_files(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "gcovr/formats/gcov/read.py", line 922, in run_gcov_and_process_files
      process_gcov_json_data(gcov_filename, covdata, options)
    File "gcovr/formats/gcov/read.py", line 294, in process_gcov_json_data
      apply_all_exclusions(file_cov, lines=encoded_source_lines, options=options)
    File "gcovr/exclusions/__init__.py", line 109, in apply_all_exclusions
      remove_internal_functions(filecov)
    File "gcovr/exclusions/__init__.py", line 136, in remove_internal_functions
      filecov.functions.pop(function.demangled_name)
  KeyError: '__gnu_cxx::__normal_iterator<char const*, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > > config::skip_list<__gnu_cxx::__normal_iterator<char const*, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > > >(__gnu_cxx::__normal_iterator<char const*, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > >, __gnu_cxx::__normal_iterator<char const*, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > >)'
