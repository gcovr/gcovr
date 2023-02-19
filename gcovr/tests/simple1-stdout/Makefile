all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase


run: txt cobertura html json json_summary coveralls

txt:
	./testcase
	$(GCOVR) -d --txt > coverage.txt

cobertura:
	./testcase
	$(GCOVR) -d -x > cobertura.xml

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
	rm -f coverage.txt coverage*.html coverage.json summary_coverage.json cobertura.xml coveralls.json
