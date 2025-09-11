include ../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp switch_test.cpp -o testcase

run: html txt json json_summary

coverage.json: coverage.json.gz
	$(GCOVR) --keep --verbose --add-tracefile $< --json-pretty --json -o $@

coverage.json.gz:
	./testcase
	$(GCOVR) --keep --verbose --decisions --json-pretty --json -o $@

json_summary: coverage.json.gz
	$(GCOVR) --keep --verbose -a $< --decisions --json-summary-pretty -o summary_coverage.json

html: coverage.json.gz
	$(GCOVR) --verbose -a $< --decisions --html-details -o coverage.html

txt: coverage.json.gz
	$(GCOVR) --verbose -a $< --txt-metric decision --txt-summary -o coverage.txt > coverage_summary.txt

json: coverage.json
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* summary_coverage.json
