include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p output && cd output && $(CXX) $(CXXFLAGS) ../main.cpp -o testcase

run: txt cobertura html sonarqube jacoco coveralls json

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

jacoco: coverage.json
	$(GCOVR) --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) --coveralls-pretty --coveralls coveralls.json

clean:
	rm -rf output
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
