GCOV ?= gcov

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json

txt: all
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d -o coverage.txt

xml: all
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d -x -o coverage.xml

html: all
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d --html-details -o coverage.html

sonarqube: all
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d --sonarqube sonarqube.xml

json: all
	# pass

clean: clean-each

clean-each:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
