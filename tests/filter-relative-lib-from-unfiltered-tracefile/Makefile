CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

BASE_OS:=$(shell uname | cut -d'-' -f1)

all: links
	cd project; $(CXX) $(CFLAGS) -c src/main.cpp -o main.o
	cd project; $(CXX) $(CFLAGS) -c ignore-this/no.cpp -o no.o
	cd project; $(CXX) $(CFLAGS) -c relevant-library/src/yes.cpp -o yes.o
	cd project; $(CXX) $(CFLAGS) main.o no.o yes.o -o testcase

run: txt lcov cobertura html sonarqube jacoco

# the src/ filter is provided by the project/gcovr.cfg configuration file
GCOVR_TEST_OPTIONS = -f '\.\./external-library/src'

coverage_unfiltered.json:
	cd project; ./testcase
	cd project; $(GCOVR) --config gcovr_empty.cfg --json-pretty --json $(abspath $@)

txt: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< -o ../coverage.txt

lcov: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --lcov ../coverage.lcov

cobertura: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --cobertura-pretty --cobertura ../cobertura.xml

html: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --html-details -o ../coverage.html

sonarqube: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --sonarqube ../sonarqube.xml

jacoco: coverage_unfiltered.json
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --jacoco ../jacoco.xml

links:
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
ifeq ($(filter $(BASE_OS),Darwin),)
	cd project; \
	   test -d relevant-library || ln -sT ../external-library relevant-library
else
	cd project; \
	   test -d relevant-library || ln -s ../external-library relevant-library
endif
else
	cmd.exe /C call setup.cmd
endif

clean:
	cd project; rm -f testcase *.gc* *.o;
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
	cd project; rm -rf relevant-library
else
	if [ -d "project/relevant-library" ]; then\
		cmd.exe /C "rmdir /S /Q project\relevant-library";\
	fi
endif
	rm -f coverage*.* cobertura.xml sonarqube.xml jacoco.xml
