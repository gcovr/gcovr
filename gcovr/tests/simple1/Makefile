all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	./testcase
	../../../scripts/gcovr --fail-under-line 80.1; test $$? -eq 2
	../../../scripts/gcovr --fail-under-branch 50.1; test $$? -eq 4
	../../../scripts/gcovr --fail-under-line 80.1 --fail-under-branch 50.1; test $$? -eq 6
	../../../scripts/gcovr --fail-under-line 79.9 --fail-under-branch 49.9
	../../../scripts/gcovr -d -o coverage.txt

xml:
	./testcase
	../../../scripts/gcovr -d -x -o coverage.xml

html:
	./testcase
	../../../scripts/gcovr -d --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html
