include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p build/a build/b
	$(CXX) $(CXXFLAGS) -c a/file1.cpp -o build/a/file1.o
	$(CXX) $(CXXFLAGS) -c b/main.cpp -o build/b/main.o
	$(CXX) $(CXXFLAGS) build/b/main.o build/a/file1.o -o testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) --gcov-exclude-directories 'build/a' --json-pretty --json $@

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
	rm -rf build  # remove *.gc* *.o
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
