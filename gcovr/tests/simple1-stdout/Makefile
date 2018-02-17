all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	./testcase
	$(GCOVR) -d > coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x > coverage.xml

html:
	./testcase
	$(GCOVR) -d --html-details > coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html
