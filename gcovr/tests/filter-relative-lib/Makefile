CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

BASE_OS:=$(shell uname | cut -d'-' -f1)

all: links
	cd project; $(CXX) $(CFLAGS) -c src/main.cpp -o main.o
	cd project; $(CXX) $(CFLAGS) -c ignore-this/no.cpp -o no.o
	cd project; $(CXX) $(CFLAGS) -c relevant-library/src/yes.cpp -o yes.o
	cd project; $(CXX) $(CFLAGS) main.o no.o yes.o -o testcase

run: txt cobertura html sonarqube coveralls

# the src/ filter is provided by the project/gcovr.cfg configuration file
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
GCOVR_TEST_OPTIONS = -f '\.\./external-library/src'
else
GCOVR_TEST_OPTIONS = -f '.*/external-library/src'
endif

coverage.json:
	cd project; ./testcase
	cd project; $(GCOVR) $(GCOVR_TEST_OPTIONS) --json-pretty --json $(abspath $@)

txt: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg --config src/gcovr_add_tracefile.cfg -o ../coverage.txt

cobertura: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg --config src/gcovr_add_tracefile.cfg --cobertura-pretty --cobertura ../cobertura.xml

html: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg --config src/gcovr_add_tracefile.cfg --html-details -o ../coverage.html

sonarqube: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg --config src/gcovr_add_tracefile.cfg --sonarqube ../sonarqube.xml

coveralls: coverage.json
	cd project; $(GCOVR) --config gcovr_empty.cfg --config src/gcovr_add_tracefile.cfg --coveralls-pretty --coveralls ../coveralls.json

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
	cd project; \
	   test -d relevant-library || cmd.exe /C "mklink /j relevant-library ..\external-library"
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
	rm -f coverage*.* cobertura.xml sonarqube.xml coveralls.json
