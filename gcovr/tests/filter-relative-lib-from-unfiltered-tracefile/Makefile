CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all: links
	cd project; $(CXX) $(CFLAGS) -c src/main.cpp -o main.o
	cd project; $(CXX) $(CFLAGS) -c ignore-this/no.cpp -o no.o
	cd project; $(CXX) $(CFLAGS) -c relevant-library/src/yes.cpp -o yes.o
	cd project; $(CXX) $(CFLAGS) main.o no.o yes.o -o testcase

run: txt xml html sonarqube

# the src/ filter is provided by the project/gcovr.cfg configuration file
GCOVR_TEST_OPTIONS = -f '\.\./external-library/src'

coverage_unfiltered.json:
	cd project; ./testcase
	cd project; $(GCOVR) --config gcovr_empty.cfg --json $(abspath $@)

txt: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< -o ../coverage.txt

xml: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< -x -o ../coverage.xml

html: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --html-details -o ../coverage.html

sonarqube: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --sonarqube ../sonarqube.xml

links:
	cd project; \
	   test -d relevant-library || ln -sT ../external-library relevant-library

clean:
	cd project; rm -f testcase *.gc* *.o; rm -rf relevant-library
	rm -f coverage*.* sonarqube.xml
