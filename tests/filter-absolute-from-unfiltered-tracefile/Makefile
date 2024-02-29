CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

BASE_OS:=$(shell uname | cut -d'-' -f1)
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
	GCOVR_TEST_OPTIONS := -f $(shell pwd)/main.cpp
else
	# "cygpath -m" is the mixed mode: Windows drive letters but forward slashes
	GCOVR_TEST_OPTIONS := -f $(shell cygpath -m "$$PWD")/main.cpp
endif

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

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
