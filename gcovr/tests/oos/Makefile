CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	mkdir -p build/src
	cd build; $(CXX) $(CFLAGS) -c ../src/file1.cpp -o src/file1.o
	cd build; $(CXX) $(CFLAGS) -c ../src/main.cpp -o src/main.o
	cd build; $(CXX) $(CFLAGS) src/main.o src/file1.o -o testcase

run: txt xml html

GCOVR_TEST_OPTIONS =

txt:
	build/testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o coverage.txt

xml:
	build/testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -x -o coverage.xml

html:
	build/testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d --html-details -o coverage.html

clean:
	rm -rf build/*
	rm -f coverage.txt coverage.xml coverage*.html
