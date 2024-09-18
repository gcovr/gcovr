include $(dir $(MAKEFILE_LIST))../common.mk

MARKER_OPT ?= --no-markers
GCOVR ?= gcovr

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt lcov cobertura html sonarqube jacoco json

txt:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) -o coverage.txt

lcov:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --lcov coverage.lcov

cobertura:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --cobertura-pretty --cobertura cobertura.xml

html:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --html-details -o coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --sonarqube sonarqube.xml

jacoco:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --jacoco jacoco.xml

json:
	./testcase
	$(GCOVR) -d $(MARKER_OPT) --json-pretty --json -o coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.css coverage*.html cobertura.xml sonarqube.xml jacoco.xml *coverage.json coverage.lcov

# mark ALL targets as phony (because they are)
.PHONY: %
