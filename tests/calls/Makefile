include $(dir $(MAKEFILE_LIST))../common.mk

all: testcase

testcase:
	$(CXX) $(CXXFLAGS) main.c -o testcase

run: json html

coverage.json:
	./testcase
	${GCOVR} --calls --json -o first.json
	./testcase
	${GCOVR} --calls --json -o second.json
	${GCOVR} --calls --json-add-tracefile first.json --json-add-tracefile second.json --json -o $@

json: coverage.json

html: coverage.json
	$(GCOVR) --calls --html --json-add-tracefile $< -o coverage.html --html-details

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.*
	rm -f *.json
