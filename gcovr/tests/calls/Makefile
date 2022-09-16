all: testcase

GCOVR ?= gcovr

testcase:
	$(CXX) -fprofile-arcs -ftest-coverage callcov.c -o testcase

run: html

# Must show calls: 63.6% (7 out of 11) in summary
coverage.html: testcase
	./testcase
	$(GCOVR) --verbose --calls --html -o coverage.html -p --print-summary --html-details

html: coverage.html
	# pass

# Targets for testing merging in json output
testcase_second:
	$(CXX) -DSECOND=1 -fprofile-arcs -ftest-coverage callcov.c -o testcase_second

report.json: testcase
	-rm callcov.gcda
	./testcase
	${GCOVR} --verbose --decisions --calls --json -o report.json -p --print-summary

second.json: testcase_second
	-rm testcase_second-callcov.gcda
	./testcase_second
	${GCOVR} --verbose --decisions --calls --json -o second.json -p --print-summary

merged.html: report.json second.json
	${GCOVR} --verbose --decisions --calls --add-tracefile report.json --add-tracefile second.json --html-details merged.html

json: report.json

merged: merged.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.*
	rm -f *.json
	rm -f merged.html
