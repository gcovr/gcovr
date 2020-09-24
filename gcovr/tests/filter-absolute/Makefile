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

run: txt xml html sonarqube coveralls

coverage.json:
	./testcase
	echo "running gcovr: $(GCOVR_TEST_OPTIONS)"
	$(GCOVR) $(GCOVR_TEST_OPTIONS) --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls coveralls.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q *.o*
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube*.*
	-cmd /C del /F /Q coveralls.json
else
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* sonarqube*.* coveralls.json
endif
