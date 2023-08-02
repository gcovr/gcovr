all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html --html-self-contained --config config/gcovr.error.config 2>&1 | grep -F "gcovr.error.config: 1: gcov-ignore-parse-errors: must be one of"
	$(GCOVR) -d --html --html-self-contained --config config/gcovr.config

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
