all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt lcov cobertura html sonarqube jacoco json json_summary coveralls

coverage.json:
	./testcase
	$(GCOVR) --verbose --gcov-keep --exclude-noncode-lines --json-pretty --json $@

json: coverage.json

txt: coverage.json
	$(GCOVR) -d -a $< --txt -o coverage.txt

lcov: coverage.json
	$(GCOVR) -d -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -d -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details coverage.html

sonarqube: coverage.json
	$(GCOVR) -d -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -d -a $< --jacoco jacoco.xml

json_summary: coverage.json
	$(GCOVR) -d -a $< --json-summary-pretty -o summary_coverage.json

coveralls: coverage.json
	$(GCOVR) -d -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage*.css cobertura.xml sonarqube.xml jacoco.xml coverage.json summary_coverage.json coveralls.json
