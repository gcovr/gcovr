include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: json txt lcov clover cobertura html sonarqube jacoco json_summary coveralls

coverage.json:
	./testcase
	$(GCOVR) --exclude-unreachable-branches --json-pretty --json $@

json: coverage.json

txt: coverage.json
	$(GCOVR) -a $< -b -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< -b --lcov coverage.lcov

clover: coverage.json
	$(GCOVR) -a $< -b --clover-pretty --clover clover.xml

cobertura: coverage.json
	$(GCOVR) -a $< -b --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< -b --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< -b --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< -b --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< -b --coveralls-pretty --coveralls coveralls.json

json_summary:
	./testcase
	$(GCOVR) --exclude-unreachable-branches -b -d --json-summary-pretty -o summary_coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f clover.xml coverage*.* cobertura*.* sonarqube*.* jacoco*.* summary_coverage.json coveralls.json
