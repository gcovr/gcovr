all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json json_summary

txt:
	./testcase
	$(GCOVR) -d --branch --fail-under-branch 100.0 -o coverage.txt

xml:
	./testcase
	$(GCOVR) -d --fail-under-branch 100.0 -x -o coverage.xml

html:
	./testcase
	$(GCOVR) -d --fail-under-branch 100.0 --html-details -o coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d --fail-under-branch 100.0 --sonarqube sonarqube.xml

json:
	# pass

json_summary:
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html sonarqube.xml
