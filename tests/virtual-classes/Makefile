include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt clover cobertura html sonarqube jacoco json json_summary coveralls

txt:
	./testcase
	$(GCOVR) -d --txt coverage.txt.gz
	gunzip -c coverage.txt.gz > coverage.txt

clover:
	./testcase
	$(GCOVR) -d --clover-pretty --clover clover.xml.gz
	gunzip -c clover.xml.gz > clover.xml

cobertura:
	./testcase
	$(GCOVR) -d --cobertura-pretty --cobertura cobertura.xml.gz
	gunzip -c cobertura.xml.gz > cobertura.xml

html:
	./testcase
	$(GCOVR) --html-details coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d --sonarqube sonarqube.xml.gz
	gunzip -c sonarqube.xml.gz > sonarqube.xml

jacoco:
	./testcase
	$(GCOVR) -d --jacoco-pretty --jacoco jacoco.xml.gz
	gunzip -c jacoco.xml.gz > jacoco.xml

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty -o summary_coverage.json.gz
	gunzip -c summary_coverage.json.gz > summary_coverage.json

json:
	./testcase
	$(GCOVR) --gcov-keep -d --json-pretty --json coverage.json.gz
	gunzip -c coverage.json.gz > coverage.json

coveralls:
	./testcase
	$(GCOVR) -d --coveralls-pretty --coveralls coveralls.json.gz
	gunzip -c coveralls.json.gz > coveralls.json

clean:
	rm -f testcase
	rm -f stderr
	rm -f *.gc*
	rm -f *coverage*.* jacoco.xml clover.xml cobertura.xml sonarqube.xml coveralls.json
