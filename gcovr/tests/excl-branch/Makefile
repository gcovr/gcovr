all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	./testcase
	$(GCOVR) --exclude-unreachable-branches -b -d -o coverage.txt

xml:
	./testcase
	$(GCOVR) --exclude-unreachable-branches -b -d -x -o coverage.xml

html:
	./testcase
	$(GCOVR) --exclude-unreachable-branches -b -d --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html
