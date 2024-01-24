all:
	$(CXX) -std=c++11 -fprofile-arcs -ftest-coverage -O0 main.cpp -o testcase

run: html txt json

coverage.json:
	./testcase
	$(GCOVR) --verbose --decisions --json-pretty --json -o coverage.json

html: coverage.json
	$(GCOVR) --verbose -a coverage.json --decisions --html-details -o coverage.html

txt: coverage.json
	$(GCOVR) --verbose -a coverage.json --txt-metric decision -o coverage.txt

json: coverage.json
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.*
