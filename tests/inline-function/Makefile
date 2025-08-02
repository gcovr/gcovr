include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: json html

json: coverage.json

coverage.json:
	./testcase
	$(GCOVR) -d --gcov-keep --json-pretty --json $@

html: coverage.json
	$(GCOVR) -d --verbose --html-details -o coverage.html --add-tracefile $<

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.*
