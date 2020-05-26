all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: csv txt xml html sonarqube json

csv:
	./testcase
	$(GCOVR) -d --csv -o coverage.csv

txt:
	# pass

xml:
	# pass

html:
	# pass

sonarqube:
	# pass

json:
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	#rm -f coverage*.csv
