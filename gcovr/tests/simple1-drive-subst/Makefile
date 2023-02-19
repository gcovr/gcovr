
GCOVR_TEST_DRIVE_WINDOWS ?=

override GCOVR += --verbose

define wrapDrive
	cmd.exe /C "subst $(GCOVR_TEST_DRIVE_WINDOWS) .."; \
	( pushd $(GCOVR_TEST_DRIVE_WINDOWS)/simple1-drive-subst && $1 ) \
	   || ( popd & cmd.exe /C "subst $(GCOVR_TEST_DRIVE_WINDOWS) /d" & exit 1 ); \
	cmd.exe /C "subst $(GCOVR_TEST_DRIVE_WINDOWS) /d"
endef

check-env :
ifeq ($(GCOVR_TEST_DRIVE_WINDOWS),)
	$(error Variable GCOVR_TEST_DRIVE_WINDOWS must be defined.)
else
	$(info Using drive $(GCOVR_TEST_DRIVE_WINDOWS).)
endif

all: check-env
	$(call wrapDrive, $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase)

run: txt cobertura html sonarqube json json_summary coveralls

txt: check-env
	$(call wrapDrive, ./testcase)
	# generate actual output
	$(call wrapDrive, $(GCOVR) -d --txt -o coverage.txt)

cobertura: check-env
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --cobertura-pretty --cobertura cobertura.xml)

html: check-env
	$(call wrapDrive, ./testcase)
	# these test cases also cover some CSS-linking permutations
	$(call wrapDrive, $(GCOVR) -d --html-details coverage-details-linkcss.html)

sonarqube: check-env
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --sonarqube sonarqube.xml)

json_summary: check-env
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --json-summary-pretty -o summary_coverage.json)

json: check-env
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --json-pretty --json coverage.json)

coveralls: check-env
	$(call wrapDrive, ./testcase)
	$(call wrapDrive, $(GCOVR) -d --coveralls-pretty --coveralls coveralls.json)

clean:
	rm -f testcase
	rm -f fail_under.stderr
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage*.css cobertura.xml sonarqube.xml coverage.json summary_coverage.json coveralls.json
