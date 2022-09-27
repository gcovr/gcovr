all: testcase

GCOVR ?= gcovr

testcase:
	$(CXX) -fprofile-arcs -ftest-coverage callcov.c -o testcase

run: html json

html: coverage.json
	$(GCOVR) --calls --html --add-tracefile $< -o coverage.html --html-details

json: coverage.json

coverage.json:
	./testcase
	${GCOVR} --calls --json -o first.json
	./testcase
	${GCOVR} --calls --json -o second.json
	${GCOVR} --calls --add-tracefile first.json --add-tracefile second.json --json -o $@

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.*
	rm -f *.json
