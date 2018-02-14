all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	./testcase
	$(GCOVR) --fail-under-line 80.1; test $$? -eq 2
	$(GCOVR) --fail-under-branch 50.1; test $$? -eq 4
	$(GCOVR) --fail-under-line 80.1 --fail-under-branch 50.1; test $$? -eq 6
	$(GCOVR) --fail-under-line 79.9 --fail-under-branch 49.9
	$(GCOVR) -d -o coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x -o coverage.xml

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html
