all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json

txt:
	./testcase
	# a couple of tests about failure thresholds
	$(GCOVR) --fail-under-line 80.1; test $$? -eq 2
	$(GCOVR) --fail-under-branch 50.1; test $$? -eq 4
	$(GCOVR) --fail-under-line 80.1 --fail-under-branch 50.1; test $$? -eq 6
	$(GCOVR) --fail-under-line 79.9 --fail-under-branch 49.9
	# generate actual output
	$(GCOVR) -d -o coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x -o coverage.xml

html:
	./testcase
	# these test cases also cover some CSS-linking permutations
	$(GCOVR) --html coverage-summary-includecss.html
	$(GCOVR) --html coverage-summary-linkcss.html --no-html-self-contained
	$(GCOVR) --html-details coverage-details-includecss.html --html-self-contained
	$(GCOVR) --html-details coverage-details-linkcss.html

sonarqube:
	./testcase
	$(GCOVR) -d --sonarqube sonarqube.xml

json:
	./testcase
	$(GCOVR) --json coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage*.css sonarqube.xml coverage.json
