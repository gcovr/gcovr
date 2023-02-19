all:
	mkdir -p output && cd output && $(CXX) -fprofile-arcs -ftest-coverage -fPIC ../main.cpp -o testcase

run: txt cobertura html sonarqube coveralls json

coverage.json:
	./output/testcase
	$(GCOVR) --json-pretty --json coverage.json

json: coverage.json

txt: coverage.json
	$(GCOVR) -o coverage.txt

cobertura: coverage.json
	$(GCOVR) --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) --coveralls-pretty --coveralls coveralls.json

clean:
	rm -rf output
	rm -f coverage*.* cobertura*.* sonarqube*.* coveralls.json
