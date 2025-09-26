include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt lcov clover cobertura html sonarqube jacoco coveralls json

coverage.json:
	./testcase
	$(GCOVR) --warn-excluded-lines-with-hits --json-pretty --json $@ 2>stderr || (cat stderr && exit 1)
	cat stderr
	grep -E "\(WARNING\) .*main.cpp:8: Line with 1 hit\(s\) excluded." stderr

json: coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< --lcov coverage.lcov

clover: coverage.json
	$(GCOVR) -a $< --clover-pretty --clover clover.xml

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --calls --html-details --html-theme github.green -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f stderr
	rm -f *.gc*
	rm -f clover.xml coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
