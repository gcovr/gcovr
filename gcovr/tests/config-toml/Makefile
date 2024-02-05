all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: html txt

html:
	./testcase
	$(GCOVR)

txt:
	./testcase
	$(GCOVR) --verbose

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.*
