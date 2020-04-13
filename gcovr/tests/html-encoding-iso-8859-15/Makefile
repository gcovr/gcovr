all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json json_summary

txt:
	# pass

xml:
	# pass

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html --source-encoding utf8 --html-encoding iso-8859-15

sonarqube:
	# pass

json:
	# pass

json_summary:
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html
