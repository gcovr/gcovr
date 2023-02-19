MARKER_OPT ?= --exclude-pattern-prefix CUSTOM
GCOVR ?= gcovr

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt cobertura html sonarqube coveralls

coverage.json:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< -o coverage.txt

cobertura: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -d $(MARKER_OPT) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* cobertura*.* sonarqube*.* coveralls.json
