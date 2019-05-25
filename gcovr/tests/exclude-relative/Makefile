CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html sonarqube

GCOVR_TEST_OPTIONS = -e 'file1.cpp'  # use a relative filter here

txt:
	./testcase
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
