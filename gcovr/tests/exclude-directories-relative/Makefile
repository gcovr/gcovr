CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	mkdir -p build/a build/b
	$(CXX) $(CFLAGS) -c a/file1.cpp -o build/a/file1.o
	$(CXX) $(CFLAGS) -c b/main.cpp -o build/b/main.o
	$(CXX) $(CFLAGS) build/b/main.o build/a/file1.o -o testcase

run: txt xml html

GCOVR_TEST_OPTIONS = --exclude-directories 'build/a'

txt:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o coverage.txt

xml:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -x -o coverage.xml

html:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage.txt coverage.xml coverage*.html
