all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

GCOVR := $(GCOVR) --txt --cobertura --sonarqube --json --json-summary --coveralls --csv -o .\\output/


run: txt xml html sonarqube json json_summary coveralls csv

txt:
	./testcase
	$(GCOVR) -d
	mv -f ./output/coverage.txt ./coverage.txt

xml:
	./testcase
	$(GCOVR) -d
	mv -f ./output/coverage.xml ./coverage.xml

html:
	./testcase
	$(GCOVR) --html
	$(GCOVR) -d --html-details
	mv -f ./output/*.html ./output/*.css ./

sonarqube:
	./testcase
	$(GCOVR) -d
	mv -f ./output/sonarqube.xml ./sonarqube.xml

json:
	./testcase
	$(GCOVR) -d
	mv -f ./output/coverage.json ./coverage.json

json_summary:
	./testcase
	$(GCOVR) -d
	mv -f ./output/summary_coverage.json ./summary_coverage.json

coveralls:
	./testcase
	$(GCOVR) -d
	mv -f ./output/coveralls.json ./coveralls.json

csv:
	./testcase
	$(GCOVR) -d
	mv -f ./output/coverage.csv ./coverage.csv

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.* coverage_details*.* cobertura.xml sonarqube.xml summary_coverage.json coveralls.json
	rm -rf output
