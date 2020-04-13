CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all: links
	cd project; $(CXX) $(CFLAGS) -c src/main.cpp -o main.o
	cd project; $(CXX) $(CFLAGS) -c ignore-this/no.cpp -o no.o
	cd project; $(CXX) $(CFLAGS) -c relevant-library/src/yes.cpp -o yes.o
	cd project; $(CXX) $(CFLAGS) main.o no.o yes.o -o testcase

run: txt xml html sonarqube json json_summary

# the src/ filter is provided by the project/gcovr.cfg configuration file
GCOVR_TEST_OPTIONS = -f '\.\./external-library/src'

txt:
	cd project; ./testcase
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o ../coverage.txt

xml:
	cd project; ./testcase
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d -x -o ../coverage.xml

html:
	cd project; ./testcase
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d --html-details -o ../coverage.html

sonarqube:
	cd project; ./testcase
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -d --sonarqube ../sonarqube.xml

json:
	# pass

json_summary:
	# pass

links:
	cd project; \
	   test -d relevant-library || ln -sT ../external-library relevant-library

clean:
	cd project; rm -f testcase *.gc* *.o; rm -rf relevant-library
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
