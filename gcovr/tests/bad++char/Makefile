all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json_summary coveralls

coverage.json:
	./testcase
	$(GCOVR) --json-pretty --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty -o summary_coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* sonarqube*.* summary_coverage.json coveralls.json
