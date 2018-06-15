all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	# pass

xml:
	# pass

html:
	./testcase
	$(GCOVR) -d --html-details --html-title="Title of report" -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html
