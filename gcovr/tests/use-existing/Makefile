GCOV ?= gcov

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d -o coverage.txt

xml:
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d -x -o coverage.xml

html:
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html
