all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

GCOVR_TEST_OPTIONS = -f '.*/tests/' -f '.*/filter.*' -r '..'

txt:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d -o coverage.txt

xml:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d -x -o coverage.xml

html:
	./testcase
	../../../scripts/gcovr $(GCOVR_TEST_OPTIONS) -d --html --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html
