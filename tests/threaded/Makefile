include $(dir $(MAKEFILE_LIST))../common.mk

GCOVR += --verbose

all:
	$(CXX) $(CXXFLAGS) -c subdir/A/file1.cpp -o subdir/A/file1.o
	$(CXX) $(CXXFLAGS) -c subdir/A/file2.cpp -o subdir/A/file2.o
	$(CXX) $(CXXFLAGS) -c subdir/A/file3.cpp -o subdir/A/file3.o
	$(CXX) $(CXXFLAGS) -c subdir/A/file4.cpp -o subdir/A/file4.o
	$(CXX) $(CXXFLAGS) -c subdir/A/file7.cpp -o subdir/A/file7.o
	$(CXX) $(CXXFLAGS) -c subdir/A/C/file5.cpp -o subdir/A/C/file5.o
	$(CXX) $(CXXFLAGS) -c subdir/A/C/D/file6.cpp -o subdir/A/C/D/file6.o
	$(CXX) $(CXXFLAGS) -c subdir/B/main.cpp -o subdir/B/main.o
	$(CXX) $(CXXFLAGS) subdir/A/file1.o subdir/A/file2.o subdir/A/file3.o subdir/A/file4.o subdir/A/C/file5.o subdir/A/C/D/file6.o subdir/A/file7.o subdir/B/main.o -o subdir/testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

# Activate verbose mode because of hanging pypy in GitHub actions
coverage.json:
	./subdir/testcase
	$(GCOVR) -j 4 -r subdir --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -r subdir -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< -r subdir --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -a $< -r subdir --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< -r subdir --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< -r subdir --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< -r subdir --jacoco jacoco.xml

coveralls:coverage.json
	$(GCOVR) -a $< -r subdir --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f ./subdir/testcase
	rm -f *.gc* */*.gc* */*/*.gc* */*/*/*.gc* */*/*/*/*.gc*
	rm -f *.o */*.o */*/*.o */*/*/*.o */*/*/*/*.o
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
