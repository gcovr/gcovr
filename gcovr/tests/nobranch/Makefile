all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube

coverage.json:
	./testcase
	$(GCOVR) --json $@

txt: coverage.json
	$(GCOVR) -a $< --branch --fail-under-branch 100.0 -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --fail-under-branch 100.0 --sonarqube sonarqube.xml

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* sonarqube*.*
