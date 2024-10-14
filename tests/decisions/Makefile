include ../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp switch_test.cpp -o testcase

run: html txt json json_summary

coverage.json:
	./testcase
	$(GCOVR) --keep --verbose --decisions --json-pretty --json -o coverage.json

json_summary: coverage.json
	$(GCOVR) --keep --verbose -a coverage.json --decisions --json-summary-pretty -o summary_coverage.json

html: coverage.json
	$(GCOVR) --verbose -a coverage.json --decisions --html-details -o coverage.html

txt: coverage.json
	$(GCOVR) --verbose -a coverage.json --txt-metric decision --txt-summary -o coverage.txt > coverage_summary.txt

json: coverage.json
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* summary_coverage.json
