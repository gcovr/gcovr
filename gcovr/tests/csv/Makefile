all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: csv

csv:
	./testcase
	$(GCOVR) -d --csv -o coverage.csv

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.csv
