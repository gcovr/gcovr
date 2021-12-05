all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: html txt

html:
	./testcase 1
	$(GCOVR) -d --html-details coverage.html

txt:
	./testcase 1
	$(GCOVR) -d --output coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage*.css
