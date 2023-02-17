MARKER_OPT ?= --no-markers
GCOVR ?= gcovr

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt cobertura html sonarqube json

txt:
	./testcase $(TESTCASE_ARGS)
	$(GCOVR) -d $(MARKER_OPT) -o coverage.txt

cobertura:
	./testcase $(TESTCASE_ARGS)
	$(GCOVR) -d $(MARKER_OPT) --cobertura-pretty --cobertura cobertura.xml

html:
	./testcase $(TESTCASE_ARGS)
	$(GCOVR) -d $(MARKER_OPT) --html-details -o coverage.html

sonarqube:
	./testcase $(TESTCASE_ARGS)
	$(GCOVR) -d $(MARKER_OPT) --sonarqube sonarqube.xml

json:
	./testcase $(TESTCASE_ARGS)
	$(GCOVR) -d $(MARKER_OPT) --json-pretty --json -o coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage*.html cobertura.xml sonarqube.xml coverage.json

# mark ALL targets as phony (because they are)
.PHONY: %
