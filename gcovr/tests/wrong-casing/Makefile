all:
	echo "Nothing to build"

run: txt xml html sonarqube json json_summary coveralls

coverage.json:
	cp main.case_1 main.case_1.gcov
	cp main.case_2 main.case_2.gcov
	$(GCOVR) --verbose --keep --use-gcov-files --json-pretty --json $@

json: coverage.json

txt: coverage.json
	$(GCOVR) -d -a $< --txt -o coverage.txt

xml: coverage.json
	$(GCOVR) -d -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details coverage.html

sonarqube: coverage.json
	$(GCOVR) -d -a $< --sonarqube sonarqube.xml

json_summary: coverage.json
	$(GCOVR) -d -a $< --json-summary-pretty -o summary_coverage.json

coveralls: coverage.json
	$(GCOVR) -d -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f *.gcov
	rm -f coverage.txt coverage.xml coverage*.html coverage*.css sonarqube.xml coverage.json summary_coverage.json coveralls.json
