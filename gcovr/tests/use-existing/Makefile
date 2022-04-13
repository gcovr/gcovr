GCOV ?= gcov

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube coveralls

coverage.json:
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -v -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -v -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -v -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -v -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -v -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* sonarqube.xml coveralls.json
