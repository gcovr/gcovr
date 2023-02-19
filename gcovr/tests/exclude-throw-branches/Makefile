all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt cobertura html sonarqube coveralls

coverage-throw.json coverage-excl-throw.json:
	./testcase
	$(GCOVR) --json-pretty --json coverage-throw.json
	$(GCOVR) --json-pretty --json coverage-excl-throw.json --exclude-throw-branches

txt: coverage-throw.json coverage-excl-throw.json
	$(GCOVR) -a coverage-throw.json -o coverage-throw.txt
	$(GCOVR) -a coverage-excl-throw.json -o coverage-excl-throw.txt

cobertura: coverage-throw.json coverage-excl-throw.json
	$(GCOVR) -x -a coverage-throw.json -o cobertura-throw.xml
	$(GCOVR) -x -a coverage-excl-throw.json -o cobertura-excl-throw.xml

html: coverage-throw.json coverage-excl-throw.json
	$(GCOVR) --html-details -a coverage-throw.json -o coverage-throw.html
	$(GCOVR) --html-details -a coverage-excl-throw.json -o coverage-excl-throw.html

sonarqube: coverage-throw.json coverage-excl-throw.json
	$(GCOVR) --sonarqube -a coverage-throw.json -o sonarqube-throw.xml
	$(GCOVR) --sonarqube -a coverage-excl-throw.json -o sonarqube-excl-throw.xml

coveralls: coverage-throw.json coverage-excl-throw.json
	$(GCOVR) --coveralls-pretty --coveralls -a coverage-throw.json -o coveralls-throw.json
	$(GCOVR) --coveralls-pretty --coveralls -a coverage-excl-throw.json -o coveralls-excl-throw.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* cobertura*.* sonarqube*.* coveralls-*.json
