include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOV) *.gcda --branch-counts --branch-probabilities --preserve-paths
	$(GCOVR) -v -g -d --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -v -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -v -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -v -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -v -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -v -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -v -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -v -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* cobertura.xml sonarqube.xml coveralls.json jacoco.xml
