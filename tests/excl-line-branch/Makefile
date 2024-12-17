TEST_DIRECTORY := $(abspath $(dir $(MAKEFILE_LIST)))
include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp foo.cpp bar.cpp -o testcase

run: json json_summary txt lcov clover cobertura html sonarqube jacoco coveralls html

coverage.json:
	./testcase
	cd ../.. ; $(GCOVR) --exclude-unreachable-branches --json-pretty --json $(TEST_DIRECTORY)/$@ $(TEST_DIRECTORY)

json: coverage.json

json_summary:
	./testcase
	cd ../.. ; $(GCOVR) --exclude-unreachable-branches -b -d --json-summary-pretty -o $(TEST_DIRECTORY)/summary_coverage.json $(TEST_DIRECTORY)

txt: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b -o $(TEST_DIRECTORY)/coverage.txt

lcov: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b --lcov $(TEST_DIRECTORY)/coverage.lcov

clover: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b --clover-pretty --clover $(TEST_DIRECTORY)/clover.xml

cobertura: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b --cobertura-pretty --cobertura $(TEST_DIRECTORY)/cobertura.xml

html: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b --html-details -o $(TEST_DIRECTORY)/coverage.html

sonarqube: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b --sonarqube $(TEST_DIRECTORY)/sonarqube.xml

jacoco: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b --jacoco $(TEST_DIRECTORY)/jacoco.xml

coveralls: coverage.json
	cd ../.. ; $(GCOVR) -a $(TEST_DIRECTORY)/$< -b --coveralls-pretty --coveralls $(TEST_DIRECTORY)/coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f clover.xml coverage*.* cobertura*.* sonarqube*.* jacoco*.* summary_coverage.json coveralls.json
