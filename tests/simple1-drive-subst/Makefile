include $(dir $(MAKEFILE_LIST))../common.mk

GCOVR_TEST_DRIVE_WINDOWS ?=

override GCOVR += --verbose

check-env :
ifeq ($(GCOVR_TEST_DRIVE_WINDOWS),)
	$(error Variable GCOVR_TEST_DRIVE_WINDOWS must be defined.)
else
	$(info Using drive $(GCOVR_TEST_DRIVE_WINDOWS).)
endif

all: check-env
	cmd.exe /C call wrap.cmd $(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt lcov cobertura html sonarqube jacoco json json_summary coveralls

txt: check-env
	cmd.exe /C call wrap.cmd testcase
	# generate actual output
	cmd.exe /C call wrap.cmd $(GCOVR) -d --txt -o coverage.txt

lcov: check-env
	cmd.exe /C call wrap.cmd testcase
	# generate actual output
	cmd.exe /C call wrap.cmd $(GCOVR) -d --lcov coverage.lcov

cobertura: check-env
	cmd.exe /C call wrap.cmd testcase
	cmd.exe /C call wrap.cmd $(GCOVR) -d --cobertura-pretty --cobertura cobertura.xml

html: check-env
	cmd.exe /C call wrap.cmd testcase
	# these test cases also cover some CSS-linking permutations
	cmd.exe /C call wrap.cmd $(GCOVR) -d --html-details coverage-details-linkcss.html

sonarqube: check-env
	cmd.exe /C call wrap.cmd testcase
	cmd.exe /C call wrap.cmd $(GCOVR) -d --sonarqube sonarqube.xml

jacoco: check-env
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --jacoco jacoco.xml)

json_summary: check-env
	cmd.exe /C call wrap.cmd testcase
	cmd.exe /C call wrap.cmd $(GCOVR) -d --json-summary-pretty -o summary_coverage.json

json: check-env
	cmd.exe /C call wrap.cmd testcase
	cmd.exe /C call wrap.cmd $(GCOVR) -d --json-pretty --json coverage.json

coveralls: check-env
	cmd.exe /C call wrap.cmd testcase
	cmd.exe /C call wrap.cmd $(GCOVR) -d --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f fail_under.stderr
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage*.css cobertura.xml sonarqube.xml jacoco.xml coverage.json summary_coverage.json coveralls.json
