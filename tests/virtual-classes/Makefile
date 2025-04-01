include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt clover cobertura html sonarqube jacoco json json_summary coveralls

txt:
	./testcase
	$(GCOVR) -d --clover-pretty --clover coverage.txt

clover:
	./testcase
	$(GCOVR) -d --clover-pretty --clover clover.xml

cobertura:
	./testcase
	$(GCOVR) -d --cobertura-pretty --cobertura cobertura.xml

html:
	./testcase
	$(GCOVR) --html-details coverage.html

sonarqube:
	./testcase
	$(GCOVR) -d --sonarqube sonarqube.xml

jacoco:
	./testcase
	$(GCOVR) -d --jacoco-pretty --jacoco jacoco.xml

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty -o summary_coverage.json

json:
	./testcase
	$(GCOVR) --gcov-keep -d --json-pretty --json coverage.json

coveralls:
	./testcase
	$(GCOVR) -d --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f stderr
	rm -f *.gc*
	rm -f *coverage*.* jacoco.xml clover.xml cobertura.xml sonarqube.xml coveralls.json
