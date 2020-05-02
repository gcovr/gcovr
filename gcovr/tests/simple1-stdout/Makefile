all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json json_summary

txt:
	./testcase
	$(GCOVR) -d > coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x > coverage.xml

html:
	./testcase
	$(GCOVR) -d --html-details > coverage.html

sonarqube:
	# pass

json:
	# pass

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty > summary_coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html summary_coverage.json
