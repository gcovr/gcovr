all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt

txt:
	./testcase
	$(GCOV) --branch-counts --branch-probabilities --all-blocks $$($(GCOV) --version | grep -F "JSON format version: 2" --silent && echo "--json-format") *.gcda
	$(GCOVR) -d --verbose --gcov-use-existing-files --txt coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt
