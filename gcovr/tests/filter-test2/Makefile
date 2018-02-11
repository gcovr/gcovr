CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

BASE_OS:=$(shell uname | cut -d'-' -f1)
ifeq ($(BASE_OS),MSYS_NT)
  GCOVR_TEST_OPTIONS := -f $(shell pwd | cygpath -w)\\main.cpp
else
  GCOVR_TEST_OPTIONS := -f $(shell pwd)/main.cpp
endif

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html

txt:
	./testcase
	echo "$(GCOVR_TEST_OPTIONS)"
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d -o coverage.txt

xml:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d -x -o coverage.xml

html:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage.txt coverage.xml coverage*.html
