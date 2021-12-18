
GCOVR_TEST_DRIVE ?= Z:

override GCOVR += --verbose

subst:
ifeq ($(wildcard $(GCOVR_TEST_DRIVE)/*.*),)
	cmd.exe /C "subst $(GCOVR_TEST_DRIVE) .." || exit 0
endif

all: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json json_summary coveralls

txt: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && ./testcase
	# generate actual output
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) -d --txt -o coverage.txt

xml: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && ./testcase
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) -d -x -o coverage.xml

html: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && ./testcase
	# these test cases also cover some CSS-linking permutations
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) --html coverage-summary-includecss.html
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) --html coverage-summary-linkcss.html --no-html-self-contained
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) --html-details coverage-details-includecss.html --html-self-contained
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) --html-details coverage-details-linkcss.html

sonarqube: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && ./testcase
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) -d --sonarqube sonarqube.xml

json_summary: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && ./testcase
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) -d --json-summary-pretty -o summary_coverage.json

json: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && ./testcase
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) --json coverage.json

coveralls: subst
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && ./testcase
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && $(GCOVR) -d --coveralls coveralls.json

clean: subst
ifneq ($(wildcard $(GCOVR_TEST_DRIVE)/*.*),)
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && rm -f testcase
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && rm -f fail_under.stderr
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && rm -f *.gc*
	cd $(GCOVR_TEST_DRIVE)/simple1-drive-subst && rm -f coverage.txt coverage.xml coverage*.html coverage*.css sonarqube.xml coverage.json summary_coverage.json coveralls.json
	cmd.exe /C "subst $(GCOVR_TEST_DRIVE) /d"
endif
