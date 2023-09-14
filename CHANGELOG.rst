``gcovr`` Release History and Change Log

.. program is needed to resolve option links
.. program::  gcovr

Next Release
------------

Known bugs:

Breaking changes:

- The exit code for an error of the reader module is changed from 8 to 64 and for a writer from 7 to 128. (:issue:`773`)

New features and notable changes:

- Add `--html-template-dir` option to use custom Jinja2 templates (:issue:`758`)
- Add block numbers and md5 sums of code lines to data model. (:issue:`764`)
- If the CSS given with :option:`--html-css` contains the string ``/* Comment.Preproc */`` no ``pygments`` CSS is added anymore. (:issue:`786`)
- Add support for ``Devcontainer`` and ``GitHub Codespaces``. (:issue:`771`)
- Fix Dockerfile.qa to avoid uid conflicts. (:issue:`801`)
- Pygments required >= 2.13.0. (:issue:`799`)
- Add a second theme for HTML report inspired by GitHub. (:issue:`793`)
- Add :option:`--fail-under-decision` and :option:`--fail-under-function` which will error under a given minimum coverage. (:issue:`773`)
- Add function coverage to data model. (:issue:`822`)
- Add support for importing Cobertura XML files with ``--cobertura-add-tracefile`` option. (:issue:`805`)
- Add :option:`--jacoco` to generate JaCoCo XML format. (:issue:`823`))
- Add function coverage to HTML report. (:issue:`828`)

Bug fixes and small improvements:

- Print calls and decision statistics in summary only if values are gathered. (:issue:`749`)
- Log the thread name if :option:`-j` is used. (:issue:`752`)
- Collapse also root directory if needed in nested HTML report. (:issue:`750`)
- Handle special case of absolute source file paths in ``gcov`` output. (:issue:`776`)
- Ignore exit code 6 when running ``gcov`` (output write error introduced gcc-12). (:issue:`781`)
- Change coveralls value from 0.0 to 1.0 if no code lines or branches are present. (:issue:`796`)
- Fix symlinked root directories on Windows. (:issue:`814`)
- Extend :option:`--gcov-ignore-errors` to be able to ignore specific gcov errors. (:issue:`787`)
- Fix reading of choices options from configuration files (e.g. ``gcov-ignore-parse-errors``). (:issue:`816`)
- Fix ``TypeError`` during decision analysis. (:issue:`784`)
- Use relative paths if possible when running ``gcov``. (:issue:`820`)

Documentation:

- Fix wrong command in ``How to create a standalone application`` docs (:issue:`792`)
- Update output html to add github style themes (:issue:`818`)

Internal changes:

- Do not scrub versions in reference data. (:issue:`747`)
- Add interface for the different formats to easily add new formats. (:issue:`755`)
- All options have now a prefix of the format and all long option names can be used in a configuration file. (:issue:`755`)

  - :option:`--txt-summary` in addition to :option:`--print-summary`
  - :option:`--json-add-tracefile` in addition to :option:`--add-tracefile`
  - :option:`--gcov-delete` in addition to :option:`--delete`
  - :option:`--gcov-keep` in addition to :option:`--keep`
  - :option:`--gcov-object-directory` in addition to :option:`--object-directory`
  - :option:`--gcov-exclude-directories` in addition to :option:`--exclude-directories`
  - :option:`--gcov-use-existing-files` in addition to :option:`--use-gcov-files`

- Use interactive terminal for docker (support of Ctrl-C to interrupt). (:issue:`767`)
- Use separate session for flake8 and us this session in lint. (:issue:`768`)
- Replace the deprecated codecov python uploader with the binary uploader. (:issue:`770`)
- Add gcc-12 and gcc-13 to the test suite. (:issue:`780`)
- Add sessions to run the targets for all versions of ``gcc`` or ``clang``. (:issue:`782`)
- Use ``build`` instead of calling ``setup.py`` directly. (:issue:`819`)

6.0 (08 March 2023)
-------------------

Known bugs:

Breaking changes:

- Remove not allowed attributes ``function-rate``, ``functions-covered`` and ``functions-valid``
  from cobertura report. (:issue:`671`)
- Remove "noncode" entries in JSON reports. (:issue:`663`)
- New :option:`--exclude-noncode-lines` to exclude noncode lines. Noncode lines are not excluded by default anymore. (:issue:`704`, :issue:`705`)
- Changed :option:`--gcov-ignore-parse-errors` to accept list of errors to ignore. (:issue:`701`)
- The default filename for :option:`--cobertura` is changed from coverage.xml to cobertura.xml (:issue:`721`)
- Handling of ``gcov`` errors:

  - Do not ignore return code of ``gcov``. (:issue:`653`)
  - New :option:`--gcov-ignore-errors` to ignore ``gcov`` errors. Old behavior was to print a warning and continue. (:issue:`718`)

- Revert changes from :issue:`623` and add documentation entry :ref:`support keil uvision format`. (:issue:`727`)

New features and notable changes:

- New :option:`--html-nested` for reports that summarize subdirectories with aggregated statistics per directory. (:issue:`687`)
- Accept `NAN %` which is used in GCOV 7.5.0 instead of an invalid value. (:issue:`651`)
- New :option:`--json-base` to define a base bath used in JSON reports. (:issue:`656`)
- New :option:`--calls` to report call coverage: function calls invoked/total (:issue:`666`)
- New nox session to generate a portable application with pyinstaller, see :ref:`standalone application`. (:issue:`661`)
- Print a warning if root directory contains symlinks. (:issue:`652`)
- Change :option:`--keep` when calling gcov internaly. (:issue:`703`)
- Allow annotations for never executed branches. (:issue:`711`)
- Add function merge mode for same function defined in different lines. (:issue:`700`)
- Update link to gcovr documentation in HTML report to point to the documentation of the used version. (:issue:`723`)
- Add environment `SOURCE_DATE_EPOCH <https://reproducible-builds.org/docs/source-date-epoch>`_ to set default for :option:`--timestamp`. (:issue:`729`)

Bug fixes and small improvements:

- Fix :option:`--html-tab-size` feature. (:issue:`650`)
- Fix alphabetical sort of html report, for when there are symlinks. (:issue:`685`)
- Handle :option:`--version` before parsing the configuration file. (:issue:`696`)
- Fix reports of excluded coverage. (:issue:`409`, :issue:`503`, :issue:`663`)
- Fix handling for nonexistent source code for HTML-details and Coveralls reports. (:issue:`663`)
- Exclude functions with :ref:`Exclusion markers`. (:issue:`713`)
- Fix problem in decision parser if open block brace is on same line. (:issue:`681`)
- Add Python 3.11 to test matrix. (:issue:`717`)
- Fix casing of files if filesystem is case insensitive. (:issue:`694`)
- Fix deadlock if :option:`-j` is used and there are errors from ``gcov`` execution. (:issue:`719`)
- Fix problem in decision parser if case is not on a single line with the break statement. (:issue:`738`)
- Do not use ``realpath`` for ``DirectoryPrefixFilter`` to support symlinks in root directory. (:issue:`712`)

Documentation:

- Add detailed reference for the JSON output format. (:issue:`663`)

Internal changes:

- Select the :option:`--html-theme` using CSS classes. (:issue:`650`)
- Change and extend ``cmake`` tests. (:issue:`676`)
- Detect ``gcc`` version for running tests. (:issue:`686`)
- Use scrubbed data for ``--update_reference`` option. (:issue:`698`)
- Install ninja with package manager instead of GitHub action. (:issue:`699`)
- Rename the reference files coverage.xml to cobertura.xml and the test from xml to cobertura (:issue:`721`)
- Add support for ``clang-14`` in our test suite and improve startup performance of docker image. (:issue:`731`)
- Compare files by extension in test suite. (:issue:`733`)
- Split HTML templates into one file for each part of the page. (:issue:`735`)
- Change docker image to be able to use it like the ``nox`` command itself. (:issue:`734`)

5.2 (06 August 2022)
--------------------

New features and notable changes:

- Log additional info on gcov parsing errors. (:issue:`589`)
- Add support for branch exclude markers. (:issue:`644`)
- Additional options to configure the thresholds for lines and branches in HTML separate. (:issue:`645`)

Bug fixes and small improvements:

- Remove function coverage from sonarcube report. (:issue:`591`)
- Fix parallel processing of gcov data. (:issue:`592`)
- Better diagnostics when dealing with corrupted input files. (:issue:`593`)
- Accept metadata lines without values (introduced in gcc-11). (:issue:`601`)
- Properly close <a> element in detailed HTML report. (:issue:`602`)
- Use `≥` sign instead of `>=` in HTML legend. (:issue:`603`)
- Using :option:`--add-tracefile` will now correctly merge branch coverage. (:issue:`600`)
- Fix package-level function coverage statistics in Cobertura XML reports. (:issue:`605`)
- Respect excluded/noncode lines for aggregated branchcoverage. (:issue:`611`)
- Fix list options in configuration file (search-path). (:issue:`612`)
- Fix assert and key error in --decisions flag. (:issue:`642`)
- Fix adding none existing lines by decision analysis to data model. (:issue:`617`)
- Always treat relative paths in config files as relative to the directory of the file. (:issue:`615`)
- More flexible ``.gcov`` parsing to support files generated by third party tools.
  (:issue:`621`, :issue:`623`)

Internal changes:

- Fix black check to fail on format errors. (:issue:`594`)
- Change session black with no arguments to format all files. (:issue:`595`)
- Add gcc-10 and gcc-11 to the test suite. (:issue:`597`)
- Improved internal coverage data model to simplify processing. (:issue:`600`)
- Use pretty print for cobertura and coveralls in test suite. (:issue:`606`)
- Forward nox options `--reuse-existing-virtualenvs` and `--no-install` to call inside docker. (:issue:`616`)

5.1 (26 March 2022)
-------------------

Breaking changes:

- Dropped support for Python 3.6 (:issue:`550`)
- Changed ``xml`` configuration key to ``cobertura`` (:issue:`552`)
- JSON summary output: all percentages are now reported from 0 to 100
  (:issue:`570`)

New features and notable changes:

- Report function coverage (:issue:`362`, :issue:`515`, :issue:`554`)
- Consistent support for symlinks across operating systems

  - Support for Windows junctions (:issue:`535`)
  - Symlinks are only resolved for :ref:`evaluating filters <filters>`
    (:issue:`565`)

- Show error message on STDERR
  when :option:`--fail-under-line` or :option:`--fail-under-branch` fails
  (:issue:`502`)
- Can report decision coverage with :option:`--decisions` option
  (reasonably formatted C/C++ source files only, HTML and JSON output)
  (:issue:`350`)
- Can create reproducible reports with the :option:`--timestamp` option
  (:issue:`546`)
- Improvements to :ref:`Exclusion markers` (LINE/START/STOP)

  - Can ignore markers in code with :option:`--no-markers` option (:issue:`361`)
  - Can customize patterns with :option:`--exclude-pattern-prefix` option
    (:issue:`561`)

- Can use :option:`--cobertura` as a less ambiguous alias for :option:`--xml`.
  (:issue:`552`)

Bug fixes and small improvements:

- Gcov is invoked without localization by setting LC_ALL=C (:issue:`513`)
- Gcov is invoked without temporary directories (:issue:`525`)
- Gcov: solved problems with file name limitations. (:issue:`528`)
- Fixed "root" path in JSON summary report. (:issue:`548`)
- Correctly resolve relative filters in configuration files. (:issue:`568`)
- HTML output: indicate lines with excluded coverage (:issue:`503`)
- HTML output: fixed sanity check to support empty files (:issue:`571`)
- HTML output: support ``jinja2 >= 3.1`` (:issue:`576`)

Documentation:

- Split documentation into smaller pages (:issue:`552`)
- Document used options for ``gcov`` (:issue:`528`)

Internal changes:

- Replaced own logger with Python's logging module. (:issue:`540`)
- New parser for ``.gcov`` file format, should be more robust. (:issue:`512`)
- New tests

  - more compilers:
    clang-10 (:issue:`484`),
    clang-13 (:issue:`527`),
    gcc-9 (:issue:`527`)
  - ``-fprofile-abs-path`` compiler option (:issue:`521`)
  - enabled symlink tests for Windows (:issue:`539`)

- Improvements to the test suite

  - Use Nox instead of Makefiles to manage QA checks (:issue:`516`, :issue:`555`)
  - Can run tests for all compiler versions in one go (:issue:`514`)
  - More linter checks (:issue:`566`)
    and code style enforcement with black (:issue:`579`)
  - Better XML diffing with yaxmldiff (:issue:`495`, :issue:`509`)
  - Share test reference data between compiler versions where possible
    (:issue:`556`)
  - Better environment variable handling (:issue:`493`, :issue:`541`)
  - Fixed glob patterns for collecting reference files (:issue:`533`)
  - Add timeout for each single test. (:issue:`572`)

- Improvements and fixes to the release process (:issue:`494`, :issue:`537`)
- Normalize shell scripts to Unix line endings (:issue:`538`, :issue:`547`)


5.0 (11 June 2021)
------------------

Breaking changes:

- Dropped support for Python 2 and Python 3.5.
  From now on, gcovr will only support Python versions
  that enjoy upstream support.

Improvements and new features:

- Handles spaces in ``gcov`` path. (:issue:`385`)
- Early fail when output cannot be created. (:issue:`382`)
- Add :option:`--txt` for text output. (:issue:`387`)
- Add :option:`--csv` for CSV output. (:issue:`376`)
- Add :option:`--exclude-lines-by-pattern` to filter out source lines by arbitrary
  regex. (:issue:`356`)
- Add :option:`--json-summary` to generate a :ref:`JSON Summary <json_summary_output>` report. (:issue:`366`)
- Add :option:`--coveralls` to generate a :ref:`Coveralls <coveralls_output>` compatible JSON report. (:issue:`328`)
- Add support for output directories. If the output ends with a ``/`` or ``\`` it is used as a directory. (:issue:`416`)
- Compare paths case insensitive if file system of working directory is case insensitive. (:issue:`329`)
- Add wildcard pattern to json :option:`--add-tracefile`. (:issue:`351`)
- Enable :option:`--filter` and :option:`--exclude` for :ref:`Merging coverage <merging_coverage>`. (:issue:`373`)
- Only output 100.0% in text and HTML output if really 100.0%, else use 99.9%. (:issue:`389`)
- Support relative source location for shadow builds. (:issue:`410`)
- Incorrect path for header now can still generate html-details reports (:issue:`271`)
- Change format version in JSON output from number to string and update it to "0.2".  (:issue:`418`, :issue:`463`)
- Only remove :option:`--root` path at the start of file paths. (:issue:`452`)
- Fix coverage report for cmake ninja builds with given in-source object-directory. (:issue:`453`)
- Add issue templates. (:issue:`461`)
- Add :option:`--exclude-function-lines` to exclude the line of the function definition in the coverage report. (:issue:`430`)
- Changes for HTML output format:

  - Redesign HTML generation. Add :option:`--html-self-contained` to control external or internal CSS. (:issue:`367`)
  - Change legend for threshold in html report. (:issue:`371`)
  - Use HTML title also for report heading. Default value for :option:`--html-title` changed. (:issue:`378`)
  - Add :option:`--html-tab-size` to configure tab size in HTML details. (:issue:`377`)
  - Add option :option:`--html-css` for user defined styling. (:issue:`380`)
  - Create details html filename independent from OS. (:issue:`375`)
  - Add :option:`--html-theme` to change the color theme. (:issue:`393`)
  - Add linkable lines in HTML details. (:issue:`401`)
  - Add syntax highlighting in the details HTML report. This can be turned off with :option:`--no-html-details-syntax-highlighting <--html-details-syntax-highlighting>`. (:issue:`402`, :issue:`415`)

Documentation:

- Cookbook: :ref:`oos cmake` (:issue:`340`, :issue:`341`)

Internal changes:

- Add makefile + dockerfile for simpler testing.
- Add .gitbugtraq to link comments to issue tracker in GUIs. (:issue:`429`)
- Add GitHub actions to test PRs and master branch. (:issue:`404`)
- Remove Travis CI. (:issue:`419`)
- Remove Appveyor CI and upload coverage report from Windows and Ubuntu from the GitHub actions. (:issue:`455`)
- Add check if commit is mentioned in the CHANGELOG.rst. (:issue:`457`)
- Move flake8 config to setup.cfg and add black code formatter. (:issue:`444`)
- Fix filter/exclude relative path issue in Windows. (:issue:`320`, :issue:`479`)
- Extend test framework for CI:

  - Set make variable TEST_OPTS as environment variable inside docker. (:issue:`372`)
  - Add make variable USE_COVERAGE to extend flags for coverage report in GitHub actions. (:issue:`404`)
  - Extend tests to use an unified diff in the assert. Add test options `--generate_reference`,
    `--update_reference` and `--skip_clean`. (:issue:`379`)
  - Support multiple output patterns in integration tests. (:issue:`383`)
  - New option `--archive_differences` to save the different files as ZIP.
    Use this ZIP as artifact in AppVeyor. (:issue:`392`)
  - Add support for gcc-8 to test suite and docker tests. (:issue:`423`)
  - Run as limited user inside docker container and add test with read only directory. (:issue:`445`)

4.2 (6 November 2019)
---------------------

Breaking changes:

- Dropped support for Python 3.4.
- Format flag parameters like :option:`--xml` or :option:`--html`
  now take an optional output file name.
  This potentially changes the interpretation of search paths.
  In ``gcovr --xml foo``,
  previous gcovr versions would search the ``foo`` directory for coverage data.
  Now, gcovr will try to write the Cobertura report to the ``foo`` file.
  To keep the old meaning, separate positional arguments like
  ``gcovr --xml -- foo``.

Improvements and new features:

- :ref:`Configuration file <configuration>` support (experimental).
  (:issue:`167`, :issue:`229`, :issue:`279`, :issue:`281`, :issue:`293`,
  :issue:`300`, :issue:`304`)
- :ref:`JSON output <json_output>`. (:issue:`301`, :issue:`321`, :issue:`326`)
- :ref:`Merging coverage <merging_coverage>`
  with :option:`gcovr --add-tracefile`.
  (:issue:`10`, :issue:`326`)
- :ref:`SonarQube XML Output <sonarqube_xml_output>`. (:issue:`308`)
- Handle cyclic symlinks correctly during coverage data search.
  (:issue:`284`)
- Simplification of :option:`--object-directory` heuristics.
  (:issue:`18`, :issue:`273`, :issue:`280`)
- Exception-only code like a ``catch`` clause is now shown as uncovered.
  (:issue:`283`)
- New :option:`--exclude-throw-branches` option
  to exclude exception handler branches. (:issue:`283`)
- Support ``--root ..`` style invocation,
  which might fix some CMake-related problems. (:issue:`294`)
- Fix wrong names in report
  when source and build directories have similar names. (:issue:`299`)
- Stricter argument handling. (:issue:`267`)
- Reduce XML memory usage by moving to lxml.
  (:issue:`1`, :issue:`118`, :issue:`307`)
- Can write :ref:`multiple reports <multiple output formats>` at the same time
  by giving the output file name to the report format parameter.
  Now, ``gcovr --html -o cov.html`` and ``gcovr --html cov.html``
  are equivalent. (:issue:`291`)
- Override gcov locale properly. (:issue:`334`)
- Make gcov parser more robust when used with GCC 8. (:issue:`315`)

Known issues:

- The :option:`--keep` option only works when using existing gcov files
  with :option:`-g`/:option:`--use-gcov-files`.
  (:issue:`285`, :issue:`286`)
- Gcovr may get confused
  when header files in different directories have the same name.
  (:issue:`271`)
- Gcovr may not work when no en_US locale is available.
  (:issue:`166`)

Documentation:

- :ref:`Exclusion marker <exclusion markers>` documentation.
- FAQ: :ref:`exception branches` (:issue:`283`)
- FAQ: :ref:`uncovered files not shown`
  (:issue:`33`, :issue:`100`, :issue:`154`, :issue:`290`, :issue:`298`)

Internal changes:

- More tests. (:issue:`269`, :issue:`268`, :issue:`269`)
- Refactoring and removal of dead code. (:issue:`280`)
- New internal data model.

4.1 (2 July 2018)
-----------------

- Fixed/improved --exclude-directories option. (:issue:`266`)
- New "Cookbook" section in the documentation. (:issue:`265`)

4.0 (17 June 2018)
------------------

Breaking changes:

- This release drops support for Python 2.6. (:issue:`250`)
- PIP is the only supported installation method.
- No longer encoding-agnostic under Python 2.7.
  If your source files do not use the system encoding (probably UTF-8),
  you will have to specify a --source-encoding.
  (:issue:`148`, :issue:`156`, :issue:`256`)
- Filters now use forward slashes as path separators, even on Windows.
  (:issue:`191`, :issue:`257`)
- Filters are no longer normalized into pseudo-paths.
  This could change the interpretation of filters in some edge cases.

Improvements and new features:

- Improved --help output. (:issue:`236`)
- Parse the GCC 8 gcov format. (:issue:`226`, :issue:`228`)
- New --source-encoding option, which fixes decoding under Python 3.
  (:issue:`256`)
- New --gcov-ignore-parse-errors flag.
  By default, gcovr will now abort upon parse errors. (:issue:`228`)
- Detect the error when gcov cannot create its output files (:issue:`243`,
  :issue:`244`)
- Add -j flag to run gcov processes in parallel. (:issue:`3`, :issue:`36`,
  :issue:`239`)
- The --html-details flag now implies --html. (:issue:`93`, :issue:`211`)
- The --html output can now be used without an --output filename
  (:issue:`223`)
- The docs are now managed with Sphinx.
  (:issue:`235`, :issue:`248`, :issue:`249`, :issue:`252`, :issue:`253`)
- New --html-title option to change the title of the HTML report.
  (:issue:`261`, :issue:`263`)
- New options --html-medium-threshold and --html-high-threshold
  to customize the color legend. (:issue:`261`, :issue:`264`)

Internal changes:

- Huge refactoring. (:issue:`214`, :issue:`215`, :issue:`221` :issue:`225`,
  :issue:`228`, :issue:`237`, :issue:`246`)
- Various testing improvements. (:issue:`213`, :issue:`214`, :issue:`216`,
  :issue:`217`, :issue:`218`, :issue:`222`, :issue:`223`, :issue:`224`,
  :issue:`227`, :issue:`240`, :issue:`241`, :issue:`245`)
- HTML reports are now rendered with Jinja2 templates. (:issue:`234`)
- New contributing guide. (:issue:`253`)

3.4 (12 February 2018)
----------------------

- Added --html-encoding command line option (:issue:`139`).
- Added --fail-under-line and --fail-under-branch options,
  which will error under a given minimum coverage. (:issue:`173`, :issue:`116`)
- Better pathname resolution heuristics for --use-gcov-file. (:issue:`146`)
- The --root option defaults to current directory '.'.
- Improved reports for "(", ")", ";" lines.
- HTML reports show full timestamp, not just date. (:issue:`165`)
- HTML reports treat 0/0 coverage as NaN, not 100% or 0%. (:issue:`105`, :issue:`149`, :issue:`196`)
- Add support for coverage-04.dtd Cobertura XML format (:issue:`164`, :issue:`186`)
- Only Python 2.6+ is supported, with 2.7+ or 3.4+ recommended. (:issue:`195`)
- Added CI testing for Windows using Appveyor. (:issue:`189`, :issue:`200`)
- Reports use forward slashes in paths, even on Windows. (:issue:`200`)
- Fix to support filtering with absolute paths.
- Fix HTML generation with Python 3. (:issue:`168`, :issue:`182`, :issue:`163`)
- Fix --html-details under Windows. (:issue:`157`)
- Fix filters under Windows. (:issue:`158`)
- Fix verbose output when using existing gcov files (:issue:`143`, :issue:`144`)


3.3 (6 August 2016)
-------------------

- Added CI testing using TravisCI
- Added more tests for out of source builds and other nested builds
- Avoid common file prefixes in HTML output (:issue:`103`)
- Added the --execlude-directories argument to exclude directories
  from the search for symlinks (:issue:`87`)
- Added branches taken/not taken to HTML (:issue:`75`)
- Use --object-directory to scan for gcov data files (:issue:`72`)
- Improved logic for nested makefiles (:issue:`135`)
- Fixed unexpected semantics with --root argument (:issue:`108`)
- More careful checks for covered lines (:issue:`109`)


3.2 (5 July 2014)
-----------------

- Adding a test for out of source builds
- Using the starting directory when processing gcov filenames.
  (:issue:`42`)
- Making relative paths the default in html output.
- Simplify html bar with coverage is zero.
- Add option for using existing gcov files (:issue:`35`)
- Fixing --root argument processing (:issue:`27`)
- Adding logic to cover branches that are ignored (:issue:`28`)


3.1 (6 December 2013)
---------------------

- Change to make the -r/--root options define the root directory
  for source files.
- Fix to apply the -p option when the --html option is used.
- Adding new option, '--exclude-unreachable-branches' that
  will exclude branches in certain lines from coverage report.
- Simplifying and standardizing the processing of linked files.
- Adding tests for deeply nested code, and symbolic links.
- Add support for multiple —filter options in same manner as —exclude
  option.


3.0 (10 August 2013)
--------------------

- Adding the '--gcov-executable' option to specify
  the name/location of the gcov executable. The command line option
  overrides the environment variable, which overrides the default 'gcov'.
- Adding an empty "<methods/>" block to <classes/> in the XML output: this
  makes out XML complient with the Cobertura DTD. (#3951)
- Allow the GCOV environment variable to override the default 'gcov'
  executable.  The default is to search the PATH for 'gcov' if the GCOV
  environment variable is not set. (#3950)
- Adding support for LCOV-style flags for excluding certain lines from
  coverage analysis. (#3942)
- Setup additional logic to test with Python 2.5.
- Added the --html and --html-details options to generate HTML.
- Sort output for XML to facilitate baseline tests.
- Added error when the --object-directory option specifies a bad directory.
- Added more flexible XML testing, which can ignore XML elements
  that frequently change (e.g. timestamps).
- Added the '—xml-pretty' option, which is used to
  generate pretty XML output for the user manual.
- Many documentation updates


2.4 (13 April 2012)
-------------------

- New approach to walking the directory tree that is more robust to
  symbolic links (#3908)
- Normalize all reported path names

  - Normalize using the full absolute path (#3921)
  - Attempt to resolve files referenced through symlinks to a common
    project-relative path

- Process ``gcno`` files when there is no corresponding ``gcda`` file to
  provide coverage information for unexecuted modules (#3887)
- Windows compatibility fixes

  - Fix for how we parse ``source:`` file names (#3913)
  - Better handling od EOL indicators (#3920)

- Fix so that gcovr cleans up all ``.gcov`` files, even those filtered by
  command line arguments
- Added compatibility with GCC 4.8 (#3918)
- Added a check to warn users who specify an empty ``--root`` option (see #3917)
- Force ``gcov`` to run with en_US localization, so the gcovr parser runs
  correctly on systems with non-English locales (#3898, #3902).
- Segregate warning/error information onto the stderr stream (#3924)
- Miscellaneous (Python 3.x) portability fixes
- Added the master svn revision number as part of the verson identifier


2.3.1 (6 January 2012)
----------------------

- Adding support for Python 3.x


2.3 (11 December 2011)
----------------------

- Adding the ``--gcov-filter`` and ``--gcov-exclude`` options.


2.2 (10 December 2011)
----------------------

- Added a test driver for gcovr.
- Improved estimation of the ``<sources>`` element when using gcovr with filters.
- Added revision and date keywords to gcovr so it is easier to identify
  what version of the script users are using (especially when they are
  running a snapshot from trunk).
- Addressed special case mentioned in [comment:ticket:3884:1]: do not
  truncate the reported file name if the filter does not start matching
  at the beginning of the string.
- Overhaul of the ``--root`` / ``--filter`` logic. This should resolve the
  issue raised in #3884, along with the more general filter issue
  raised in [comment:ticket:3884:1]
- Overhaul of gcovr's logic for determining gcc/g++'s original working
  directory. This resolves issues introduced in the original
  implementation of ``--object-directory`` (#3872, #3883).
- Bugfix: gcovr was only including a ``<sources>`` element in the XML
  report if the user specified ``-r`` (#3869)
- Adding timestamp and version attributes to the gcovr XML report (see
  #3877).  It looks like the standard Cobertura output reports number of
  seconds since the epoch for the timestamp and a doted decimal version
  string.  Now, gcovr reports seconds since the epoch and
  "``gcovr ``"+``__version__`` (e.g. "gcovr 2.2") to differentiate it
  from a pure Cobertura report.


2.1 (26 November 2010)
----------------------

- Added the ``--object-directory`` option, which allows for a flexible
  specification of the directory that contains the objects generated by
  gcov.
- Adding fix to compare the absolute path of a filename to an exclusion
  pattern.
- Adding error checking when no coverage results are found. The line and
  branch counts can be zero.
- Adding logic to process the ``-o``/``--output`` option (#3870).
- Adding patch to scan for lines that look like::

       creating `foo'

  as well as
  ::

       creating 'foo'

- Changing the semantics for EOL to be portable for MS Windows.
- Add attributes to xml format so that it could be used by hudson/bamboo with
  cobertura plug-in.


2.0 (22 August 2010)
--------------------

- Initial release as a separate package.  Earlier versions of gcovr
  were managed within the 'fast' Python package.
