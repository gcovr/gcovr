include $(dir $(MAKEFILE_LIST))../common.mk


all:
	$(CXX) $(CXXFLAGS) $(if $(USE_LAMBDA),-std=c++20 -DUSE_LAMBDA,) main.cpp -o testcase

run: json txt lcov clover cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) -v --gcov-keep --json-pretty --json $@

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
	$(GCOVR) -a $< --jacoco-pretty --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -f *.gc* stderr
	rm -f clover.xml coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
