CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

ifeq ($(OS),Windows_NT)
	SHELL=cmd
	GCOVR_TEST_OPTIONS := -f $(subst \,/,$(shell cd))/main.cpp
else
	BASE_OS:=$(shell uname | cut -d'-' -f1)
	ifneq (,$(findstring MINGW,$(BASE_OS)))
		BASE_OS:=MSYS_NT
	endif
	ifeq ($(BASE_OS),MSYS_NT)
		# "cygpath -m" is the mixed mode: Windows drive letters but forward slashes
		GCOVR_TEST_OPTIONS := -f $(shell cygpath -m "$$PWD")/main.cpp
	else
		GCOVR_TEST_OPTIONS := -f $(shell pwd)/main.cpp
	endif
endif

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html sonarqube

coverage_unfiltered.json:
	./testcase
	$(GCOVR) --json $@

txt: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< -o coverage.txt

xml: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< -x -o coverage.xml

html: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --html-details -o coverage.html

sonarqube: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --sonarqube sonarqube.xml

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q *.o*
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube*.*
else
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* sonarqube*.*
endif
