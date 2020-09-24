CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

# the src/ filter is provided by the project/gcovr.cfg configuration file
ifeq ($(OS),Windows_NT)
	GCOVR_TEST_OPTIONS= -f "../external-library/src"
else
	GCOVR_TEST_OPTIONS= -f '../external-library/src'
endif

all: links
	cd project && $(CXX) $(CFLAGS) -c src/main.cpp -o main.o
	cd project && $(CXX) $(CFLAGS) -c ignore-this/no.cpp -o no.o
	cd project && $(CXX) $(CFLAGS) -c relevant-library/src/yes.cpp -o yes.o
	cd project && $(CXX) $(CFLAGS) main.o no.o yes.o -o testcase

run: txt xml html sonarqube

coverage_unfiltered.json:
	cd project && testcase
	cd project && $(GCOVR) --config gcovr_empty.cfg --json $(abspath $@)

txt: coverage_unfiltered.json
	cd project && $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< -o ../coverage.txt

xml: coverage_unfiltered.json
	cd project && $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< -x -o ../coverage.xml

html: coverage_unfiltered.json
	cd project && $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --html-details -o ../coverage.html

sonarqube: coverage_unfiltered.json
	cd project && $(GCOVR) $(GCOVR_TEST_OPTIONS) -a ../$< --sonarqube ../sonarqube.xml

links:
ifeq ($(OS),Windows_NT)
	cmd /C mklink /d project\relevant-library $(shell cd)\external-library
else
	cd project; test -d relevant-library || ln -sT ../external-library relevant-library
endif

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q /S project\testcase*
	-cmd /C del /F /Q project\\*.gc*
	-cmd /C del /F /Q project\\*.o*
	-cmd /C rmdir /Q project\relevant-library
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube.xml
else
	cd project; rm -f testcase *.gc* *.o; rm -rf relevant-library
	rm -f coverage*.* sonarqube.xml
endif

