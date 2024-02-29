all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: html txt

html:
	./testcase
	$(GCOVR) -d --html-details coverage.html

txt:
	./testcase
	$(GCOVR) -d --output coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage*.css
