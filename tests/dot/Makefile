include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) -c .subdir/A/file1.cpp -o .subdir/A/file1.o
	$(CXX) $(CXXFLAGS) -c .subdir/A/file2.cpp -o .subdir/A/file2.o
	$(CXX) $(CXXFLAGS) -c .subdir/A/file3.cpp -o .subdir/A/file3.o
	$(CXX) $(CXXFLAGS) -c .subdir/A/file4.cpp -o .subdir/A/file4.o
	$(CXX) $(CXXFLAGS) -c .subdir/A/C/file5.cpp -o .subdir/A/C/file5.o
	$(CXX) $(CXXFLAGS) -c .subdir/A/C/D/file6.cpp -o .subdir/A/C/D/file6.o
	$(CXX) $(CXXFLAGS) -c .subdir/B/main.cpp -o .subdir/B/main.o
	$(CXX) $(CXXFLAGS) .subdir/A/file1.o .subdir/A/file2.o .subdir/A/file3.o .subdir/A/file4.o .subdir/A/C/file5.o .subdir/A/C/D/file6.o .subdir/B/main.o -o .subdir/testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	.subdir/testcase
	$(GCOVR) -r . --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -r . -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -r . -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -r . -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -r . -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -r . -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -r . -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -r . -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f ./.subdir/testcase
	find .subdir -name '*.gc*' -delete
	find .subdir -name '*.o' -delete
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
