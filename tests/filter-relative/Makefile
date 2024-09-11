include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CXXFLAGS) -c main.cpp -o main.o
	$(CXX) $(CXXFLAGS) main.o file1.o -o testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) -f 'main.cpp' --json-pretty --json $@  # use a relative filter here

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< --lcov coverage.lcov

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
	rm -f testcase
	rm -f *.gc* *.o
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
