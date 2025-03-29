include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt clover cobertura html sonarqube jacoco json json_summary coveralls

txt:
	./testcase
	$(GCOVR) -d --clover-pretty --clover coverage.txt

clover:
	./testcase
	$(GCOVR) -d --clover-pretty --clover clover.xml

cobertura:
	./testcase
	$(GCOVR) -d --cobertura-pretty --cobertura cobertura.xml

html:
	./testcase
	$(GCOVR) --html-details coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d --sonarqube sonarqube.xml

jacoco:
	./testcase
	$(GCOVR) -d --jacoco-pretty --jacoco jacoco.xml

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty -o summary_coverage.json

json:
	./testcase
	$(GCOVR) --gcov-keep -d --json-pretty --json coverage.json
ifeq ($(CC_REFERENCE),gcc-14)
	echo "Try to merge with single mangled name"
	$(GCOVR) -d --json-pretty -a coverage.json -a reference/gcc-5/coverage.json --json coverage.merged.single_mangled_name.json 2>stderr ; test $$? -eq 64 || ( cat stderr ; exit 1 )
	grep -F "AssertionError: Mangled function name main only defined in one file. This can be ignored by --merge-mode-function-names=ignore-single-definition." stderr || ( cat stderr ; exit 1 )
	$(GCOVR) -d --json-pretty -a coverage.json -a reference/gcc-5/coverage.json --merge-mode-function-names=ignore-single-definition --json coverage.merged.single_mangled_name.json

	echo "Try to merge with single demangled name"
	sed -e '/demangled_name/ d' coverage.json > coverage.single_demangled_name.json
	$(GCOVR) -d --json-pretty -a coverage.json -a coverage.single_demangled_name.json --json coverage.merged.single_demangled_name.json 2>stderr ; test $$? -eq 64 || ( cat stderr ; exit 1 )
	grep -F "AssertionError: Demangled function name main only defined in one file. This can be ignored by --merge-mode-function-names=ignore-single-definition." stderr || ( cat stderr ; exit 1 )
	$(GCOVR) -d --json-pretty -a coverage.json -a coverage.single_demangled_name.json --merge-mode-function-names=ignore-single-definition --json coverage.merged.single_demangled_name.json

	echo "Try to merge with unmatched mangled name"
	sed -e 's/_ZN3ns14Bar1C2Ev/_ZN3ns14Bar1C2Ev_mod/' coverage.json > coverage.demangled_name_mismatch.json
	$(GCOVR) -d --json-pretty -a coverage.json -a coverage.demangled_name_mismatch.json --json coverage.not_written.json 2>stderr ; test $$? -eq 64 || ( cat stderr ; exit 1 )
	grep -E "AssertionError: Function name in .+/tests/virtual-classes/main.cpp:8 must be _ZN3ns14Bar1C2Ev(_mod)?, got _ZN3ns14Bar1C2Ev(_mod)?." stderr || ( cat stderr ; exit 1 )
endif

coveralls:
	./testcase
	$(GCOVR) -d --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f stderr
	rm -f *.gc*
	rm -f *coverage*.* jacoco.xml clover.xml cobertura.xml sonarqube.xml coveralls.json
