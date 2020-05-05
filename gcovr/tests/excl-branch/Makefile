all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube

txt: coverage.json
	$(GCOVR) -a $< -b -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -b -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< -b --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< -b --sonarqube sonarqube.xml

coverage.json:
	./testcase
	$(GCOVR) --exclude-unreachable-branches --json $@

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* sonarqube*.*
