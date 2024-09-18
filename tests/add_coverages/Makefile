include $(dir $(MAKEFILE_LIST))../common.mk

export GCOVR_TEST_SUITE_NO_GIT_COMMAND := 1

all:
	$(CXX) $(CXXFLAGS) -c foo.cpp -o foo.o
	$(CXX) $(CXXFLAGS) -c bar.cpp -o bar.o
	$(CXX) $(CXXFLAGS) -DFOO -c main.cpp -o main_foo.o
	$(CXX) $(CXXFLAGS) main_foo.o foo.o -o testcase_foo
	$(CXX) $(CXXFLAGS) -DBAR -c main.cpp -o main_bar.o
	$(CXX) $(CXXFLAGS) main_bar.o bar.o -o testcase_bar

run: txt cobertura html sonarqube jacoco json json_summary coveralls

# Enable JSON output via the --json-pretty --json mode.
# However, this option cannot take a filename directly
# so that "-o" is used.
coverage_foo.json:
	./testcase_foo
	$(GCOVR) -d --json-pretty -o $@

# Just use --json-pretty and --json and pass the output filename directly.
coverage_bar.json: coverage_foo.json
	./testcase_bar
	$(GCOVR) -d --json-pretty --json $@

txt: coverage_foo.json coverage_bar.json
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json -o coverage.txt

cobertura: coverage_foo.json coverage_bar.json
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --cobertura-pretty --cobertura cobertura.xml

html: coverage_foo.json coverage_bar.json
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --html-details -o coverage.html

sonarqube: coverage_foo.json coverage_bar.json
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --sonarqube sonarqube.xml

jacoco: coverage_foo.json coverage_bar.json
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --jacoco jacoco.xml --jacoco-pretty

# Use both --json-pretty --json here
json: coverage_foo.json coverage_bar.json
	$(GCOVR) -a 'coverage_*.json' --json-pretty --json coverage.json

json_summary: coverage_foo.json coverage_bar.json
	$(GCOVR) -a 'coverage_*.json' --json-summary-pretty -o summary_coverage.json

coveralls: coverage_foo.json coverage_bar.json
	$(GCOVR) -a coverage_foo.json -a coverage_bar.json --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase_*
	rm -f *.gc*
	rm -f *.o
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* summary_coverage.json coveralls.json
