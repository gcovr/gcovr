MARKER_OPT ?= --exclude-pattern-prefix CUSTOM
GCOVR ?= gcovr

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt lcov clover cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --lcov coverage.lcov

clover: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --clover-pretty --clover clover.xml

cobertura: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f clover.xml coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
