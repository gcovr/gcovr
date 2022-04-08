all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase


run: txt xml html json json_summary coveralls

txt:
	./testcase
	$(GCOVR) -d --txt > coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x > coverage.xml

html:
	./testcase
	$(GCOVR) -d --html > coverage.html

json:
	./testcase
	$(GCOVR) --json-pretty --json > coverage.json

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty > summary_coverage.json

coveralls:
	./testcase
	$(GCOVR) -d --coveralls-pretty --coveralls > coveralls.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage.json summary_coverage.json coveralls.json
