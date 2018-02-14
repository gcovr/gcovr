CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	mkdir -p build
	$(CXX) $(CFLAGS) -c src/file1.cpp -o build/file1.o
	$(CXX) $(CFLAGS) -c src/main.cpp -o build/main.o
	$(CXX) $(CFLAGS) build/main.o build/file1.o -o build/testcase

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
	rm -f build/*
	rm -f coverage.txt coverage.xml coverage*.html
