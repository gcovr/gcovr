include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p build
	$(CXX) $(CXXFLAGS) -c src/file1.cpp -o build/file1.o
	$(CXX) $(CXXFLAGS) -c src/main.cpp -o build/main.o
	$(CXX) $(CXXFLAGS) build/main.o build/file1.o -o build/testcase

run: txt lcov cobertura html sonarqube jacoco json_summary coveralls


coverage.json:
	build/testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

json_summary:
	build/testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d --json-summary -o summary_coverage.json

clean:
	rm -f build/*
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* summary_coverage.json coveralls.json
