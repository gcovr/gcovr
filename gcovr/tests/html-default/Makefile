all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: html css

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html

css:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
