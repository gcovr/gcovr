all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html json

txt:
	./testcase
	$(GCOVR) -d > coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x > coverage.xml

html:
	./testcase
	$(GCOVR) -d --html > coverage.html

json:
	./testcase
	$(GCOVR) --json > coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage.json
