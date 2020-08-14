CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all: links
	cd project; $(CXX) $(CFLAGS) -c src/main.cpp -o main.o
	cd project; $(CXX) $(CFLAGS) -c ignore-this/no.cpp -o no.o
	cd project; $(CXX) $(CFLAGS) -c relevant-library/src/yes.cpp -o yes.o
	cd project; $(CXX) $(CFLAGS) main.o no.o yes.o -o testcase

run: txt xml html sonarqube coveralls

# the src/ filter is provided by the project/gcovr.cfg configuration file
GCOVR_TEST_OPTIONS = -f '\.\./external-library/src'

coverage.json:
	cd project; ./testcase
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) --json $(abspath $@)

txt: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg -a ../coverage.json -o ../coverage.txt

xml: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg -a ../coverage.json -x -o ../coverage.xml

html: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg -a ../coverage.json --html-details -o ../coverage.html

sonarqube: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg -a ../coverage.json --sonarqube ../sonarqube.xml

coveralls: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg -a ../coverage.json --coveralls ../coveralls.json

links:
	cd project; \
	   test -d relevant-library || ln -sT ../external-library relevant-library

clean:
	cd project; rm -f testcase *.gc* *.o; rm -rf relevant-library
	rm -f coverage*.* sonarqube.xml coveralls.json
