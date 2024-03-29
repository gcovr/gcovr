all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt lcov cobertura html sonarqube jacoco json_summary coveralls

coverage.json:
	./testcase
	$(GCOVR) --exclude-unreachable-branches --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -b -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< -b --lcov coverage.lcov

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
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* summary_coverage.json coveralls.json
