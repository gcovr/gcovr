include $(dir $(MAKEFILE_LIST))../common.mk

USE_LAMBDA := $(shell ($(CC) --help --verbose 2>&1 | grep -F "c++20" --silent) && echo 1)

all:
	$(CXX) $(CXXFLAGS) $(if $(USE_LAMBDA),-std=c++20 -DUSE_LAMBDA,) main.cpp -o testcase

run: json txt lcov clover cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) -v --gcov-keep --exclude-function 'sort_excluded_both()::{lambda(int, int)#2}::operator()(int, int) const' --exclude-function '/bar.+/' --json-pretty --json $@ 2>stderr || (cat stderr && exit 1)
	cat stderr
# If pos entry is found the compiler supports the function position else we need to see a warning.
	grep -F '"pos"' --silent $@ || grep -F "Function exclude marker found on line 9:8 but not supported for this compiler" stderr
	grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 9:8 but not supported for this compiler" stderr || exit 0
	grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 9:8 but no function definition found" stderr || exit 0
	grep -F '"pos"' --silent $@ || grep -F "Function exclude marker found on line 9:51 but not supported for this compiler" stderr
	grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 9:51 but not supported for this compiler" stderr || exit 0
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ || grep -F "Function exclude marker found on line 44:29 but not supported for this compiler" stderr,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 44:29 but not supported for this compiler" stderr || exit 0,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ || grep -F "Function exclude marker found on line 50:19 but not supported for this compiler" stderr,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 50:19 but no function definition found" stderr || exit 0,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ || grep -F "Function exclude marker found on line 57:29 but not supported for this compiler" stderr,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 57:29 but not supported for this compiler" stderr || exit 0,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ || grep -F "Function exclude marker found on line 66:34 but not supported for this compiler" stderr,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 66:34 but not supported for this compiler" stderr || exit 0,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ || grep -F "Function exclude marker found on line 73:29 but not supported for this compiler" stderr,)
	$(if $(USE_LAMBDA),grep -F '"pos"' --silent $@ && grep -F "Function exclude marker found on line 73:29 but not supported for this compiler" stderr || exit 0,)
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
	rm -f testcase
	rm -f *.gc* stderr
	rm -f clover.xml coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
