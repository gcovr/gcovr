all:
	$(CXX) -fprofile-arcs -ftest-coverage callcov.c -o testcase

run: html

# Must show calls: 63.6% (7 out of 11) in summary
coverage.html:
	./testcase
	$(GCOVR) --verbose --calls --html -o coverage.html -p --print-summary --html-details

html: coverage.html
	# pass

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.*
