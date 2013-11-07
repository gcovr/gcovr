all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	./testcase
	../../../scripts/gcovr --exclude-unreachable-branches -b -r . -d -o coverage.txt

xml:
	./testcase
	../../../scripts/gcovr --exclude-unreachable-branches -b -r . -d -x -o coverage.xml

html:
	./testcase
	../../../scripts/gcovr --exclude-unreachable-branches -b -r . -d --html --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html
