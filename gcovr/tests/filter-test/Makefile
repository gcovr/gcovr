CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html

GCOVR_TEST_OPTIONS = -f '.*main.cpp'

txt:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d -o coverage.txt

xml:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d -x -o coverage.xml

html:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d --html --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage.txt coverage.xml coverage*.html
