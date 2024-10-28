include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) -c code.cpp -o code.o
	cat test.cpp | $(CXX) $(CXXFLAGS) -x c++ -c - -o test.o
	$(CXX) $(CXXFLAGS) code.o test.o -o testcase

run: txt lcov cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) --gcov-keep --verbose $$(if [ "$${CC_REFERENCE:=$$CC}" != "gcc-14" ] ; then echo "--gcov-ignore-errors no_working_dir_found" ; fi) --json-pretty --json coverage.json

txt: coverage.json
	$(GCOVR) -a '$<.not_exists' 2>no_tracefile.stderr; test $$? -eq 64 || ( cat no_tracefile.stderr & exit 1 )
	grep -F "Bad --json-add-tracefile option." no_tracefile.stderr
	grep -F "The specified file does not exist." no_tracefile.stderr
	$(GCOVR) -a $< -o coverage.txt

lcov: coverage.json
	$(GCOVR) -a $< --lcov coverage.lcov

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<  --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco -o jacoco.xml

clean:
	rm -rf *.gc* *.o
	rm -f no_tracefile.stderr testcase coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
