
GCOVR_TEST_DRIVE_WINDOWS ?=
ifeq ($(GCOVR_TEST_DRIVE_WINDOWS),)
$(error Variable GCOVR_TEST_DRIVE_WINDOWS must be defined.)
endif

override GCOVR += --verbose

define wrapDrive
	cmd.exe /C "subst $(GCOVR_TEST_DRIVE_WINDOWS) .."; \
	( pushd $(GCOVR_TEST_DRIVE_WINDOWS)/simple1-drive-subst && $1 ) \
	   || ( popd & cmd.exe /C "subst $(GCOVR_TEST_DRIVE_WINDOWS) /d" & exit 1 ); \
	cmd.exe /C "subst $(GCOVR_TEST_DRIVE_WINDOWS) /d"
endef

all:
	$(call wrapDrive, $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase)

run: txt xml html sonarqube json json_summary coveralls

txt:
	$(call wrapDrive, ./testcase)
	# generate actual output
	$(call wrapDrive, $(GCOVR) -d --txt -o coverage.txt)

xml:
	$(call wrapDrive, ./testcase
	$(call wrapDrive, $(GCOVR) -d -x -o coverage.xml)

html:
	$(call wrapDrive, ./testcase)
	# these test cases also cover some CSS-linking permutations
	$(call wrapDrive, $(GCOVR) --html-details coverage-details-linkcss.html)

sonarqube:
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --sonarqube sonarqube.xml)

json_summary:
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --json-summary-pretty -o summary_coverage.json)

json:
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) --json coverage.json)

coveralls:
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --coveralls coveralls.json)

clean:
	rm -f testcase
	rm -f fail_under.stderr
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage*.css sonarqube.xml coverage.json summary_coverage.json coveralls.json
