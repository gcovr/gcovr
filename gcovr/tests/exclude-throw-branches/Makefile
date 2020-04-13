all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json json_summary

txt:
	./testcase
	$(GCOVR) -b                             -o coverage-throw.txt
	$(GCOVR) -b -d --exclude-throw-branches -o coverage-excl-throw.txt

xml:
	./testcase
	$(GCOVR)    -x                          -o coverage-throw.xml
	$(GCOVR) -d -x --exclude-throw-branches -o coverage-excl-throw.xml

html:
	./testcase
	$(GCOVR)    --html-details                          -o coverage-throw.html
	$(GCOVR) -d --html-details --exclude-throw-branches -o coverage-excl-throw.html

sonarqube:
	./testcase
	$(GCOVR)			     --sonarqube sonarqube-throw.xml
	$(GCOVR) -d --exclude-throw-branches --sonarqube sonarqube-excl-throw.xml

json:
	# pass

json_summary:
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage-*.txt coverage-*.xml coverage-*.html sonarqube-*.xml
