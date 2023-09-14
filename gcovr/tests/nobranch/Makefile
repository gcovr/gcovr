all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< --branch --fail-under-branch 100.0 -o coverage.txt

cobertura: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
