include $(dir $(MAKEFILE_LIST))../common.mk

GCOVR_TEST_OPTIONS = -f 'main.cpp'

all:
	$(CXX) $(CXXFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CXXFLAGS) -c main.cpp -o main.o
	$(CXX) $(CXXFLAGS) main.o file1.o -o testcase

run: txt lcov cobertura html sonarqube jacoco

coverage_unfiltered.json:
	./testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< -o coverage.txt

lcov: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --lcov coverage.lcov

cobertura: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --html-details -o coverage.html

sonarqube: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --sonarqube sonarqube.xml

jacoco: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --jacoco jacoco.xml

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.*
