
UNCOVERED_MESSAGE := $(if $(filter __CLANG__,$(shell $(CC) --version | grep -F "clang version" && echo __CLANG__)),2 out of 4,3 out of 6)

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: json txt lcov clover cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) -v --json-pretty --json $@ 2>stderr && cat stderr
	grep -F "4:7 without coverage information" stderr
	grep -F ":5:24 is excluding 3 branch(es)" stderr
	grep -E "\(2/6\) at .*:20:31 is wrong. There are $(UNCOVERED_MESSAGE) branches uncovered" stderr

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
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase stderr
	rm -f *.gc*
	rm -f clover.xml coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
