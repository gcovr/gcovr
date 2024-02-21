
BASE_OS:=$(shell uname | cut -d'-' -f1)

CC_REFERENCE ?= $(notdir $(CC))
FAIL_UNDER_LINE := $(shell cat reference/$(CC_REFERENCE)$(if $(filter $(BASE_OS),MSYS_NT MINGW64_NT),-Windows,)/fail_under)

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt clover cobertura html sonarqube jacoco json json_summary coveralls

txt:
	./testcase
	# a couple of tests about failure thresholds
	$(GCOVR) --fail-under-line 80.1 --print-summary 2>fail_under.stderr; test $$? -eq 2 || ( cat fail_under.stderr & exit 1 )
	grep -F "failed minimum line coverage" fail_under.stderr
	$(GCOVR) --fail-under-branch 50.1 --print-summary 2>fail_under.stderr; test $$? -eq 4 || ( cat fail_under.stderr & exit 1 )
	grep -F "failed minimum branch coverage" fail_under.stderr
	$(GCOVR) --decision --fail-under-decision 50.1 --print-summary 2>fail_under.stderr; test $$? -eq 8 || ( cat fail_under.stderr & exit 1 )
	grep -F "failed minimum decision coverage" fail_under.stderr
	$(GCOVR) --fail-under-function 100 --print-summary 2>fail_under.stderr; test $$? -eq 16 || ( cat fail_under.stderr & exit 1 )
	grep -F "failed minimum function coverage" fail_under.stderr
	$(GCOVR) --fail-under-line 80.1 --fail-under-branch 50.1 --decision --fail-under-decision 50.1 --fail-under-function 100 --print-summary 2>fail_under.stderr; test $$? -eq 30 || ( cat fail_under.stderr & exit 1 )
	grep -F "failed minimum line coverage" fail_under.stderr
	grep -F "failed minimum branch coverage" fail_under.stderr
	grep -F "failed minimum decision coverage" fail_under.stderr
	grep -F "failed minimum function coverage" fail_under.stderr
	$(GCOVR) --fail-under-line $(FAIL_UNDER_LINE) --fail-under-branch 49.9 --print-summary 2>fail_under.stderr; test $$? -eq 0 || ( cat fail_under.stderr & exit 1 )
	grep -F "failed minimum line coverage" fail_under.stderr; test $$? -eq 1
	grep -F "failed minimum branch coverage" fail_under.stderr; test $$? -eq 1
	grep -F "failed minimum decision coverage" fail_under.stderr; test $$? -eq 1
	grep -F "failed minimum function coverage" fail_under.stderr; test $$? -eq 1
	# generate actual output
	$(GCOVR) -d --txt -o coverage.txt

clover:
	./testcase
	$(GCOVR) -d --clover-pretty --clover clover.xml

cobertura:
	./testcase
	$(GCOVR) -d --cobertura-pretty --cobertura cobertura.xml

html:
	./testcase
	# these test cases also cover some CSS-linking permutations
	$(GCOVR) --html coverage-summary-includecss.html
	$(GCOVR) --html coverage-summary-linkcss.html --no-html-self-contained
	$(GCOVR) --html-details coverage-details-includecss.html --html-self-contained
	$(GCOVR) -d --html-details coverage-details-linkcss.html

sonarqube:
	./testcase
	$(GCOVR) -d --sonarqube sonarqube.xml

jacoco:
	./testcase
	$(GCOVR) -d --jacoco-pretty --jacoco jacoco.xml

json_summary:
	./testcase
	$(GCOVR) -d --json-base test\\dir --json-summary-pretty -o summary_coverage.json

json:
	./testcase
	$(GCOVR) -d --json-base test\\dir --json-pretty --json coverage.json

coveralls:
	./testcase
	$(GCOVR) -d --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f fail_under.stderr
	rm -f *.gc*
	rm -f coverage.txt jacoco.xml coverage*.html coverage*.css cobertura.xml sonarqube.xml coverage.json summary_coverage.json coveralls.json
