include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: json txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) --gcov-keep --decision -v --json-pretty --json $@
	$(GCOVR) --gcov-keep --merge-lines --decision -v --json-pretty --json coverage.merged.json
	diff -U 1 $@ coverage.merged.json

json: coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt
	$(GCOVR) -a $< --merge-lines -o coverage.merged.txt

lcov: coverage.json
	$(GCOVR) -a $< --lcov coverage.lcov
	$(GCOVR) -a $< --merge-lines --lcov coverage.merged.lcov

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml
	$(GCOVR) -a $< --merge-lines --cobertura-pretty --cobertura cobertura.merged.xml

html: coverage.json
	$(GCOVR) -a $< --decision --html-self-contained --html-single-page --html-details -o coverage.html
	$(GCOVR) -a $< --merge-lines --decision --html-self-contained --html-single-page --html-details -o coverage.merged.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml
	$(GCOVR) -a $< --merge-lines --sonarqube sonarqube.merged.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco jacoco.xml
	$(GCOVR) -a $< --merge-lines --jacoco jacoco.merged.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json
	$(GCOVR) -a $< --merge-lines --coveralls-pretty --coveralls coveralls.merged.json

clean:
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls*.json
