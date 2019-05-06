CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

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

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html sonarqube

txt:
	./testcase
	echo "$(GCOVR_TEST_OPTIONS)"
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o coverage.txt

xml:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -x -o coverage.xml

html:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d --html-details -o coverage.html

sonarqube:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d --sonarqube sonarqube.xml

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
