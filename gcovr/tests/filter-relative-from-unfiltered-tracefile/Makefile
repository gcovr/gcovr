CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

GCOVR_TEST_OPTIONS = -f 'main.cpp'

all:
	$(CXX) $(CFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CFLAGS) -c main.cpp -o main.o
	$(CXX) $(CFLAGS) main.o file1.o -o testcase

run: txt xml html sonarqube

coverage_unfiltered.json:
	./testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< -o coverage.txt

xml: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --html-details -o coverage.html

sonarqube: coverage_unfiltered.json
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -a $< --sonarqube sonarqube.xml

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* sonarqube*.*
