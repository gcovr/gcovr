all:
	$(CXX) -fprofile-arcs -ftest-coverage main.cpp -o testcase

run: html json

html: json
	./testcase
	$(GCOVR) --verbose -a coverage.json --decisions --html-details -o coverage.html

json:
	./testcase
	$(GCOVR) --verbose  --decisions --json -o coverage.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* sonarqube.xml
