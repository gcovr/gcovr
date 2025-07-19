include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: json txt lcov cobertura html sonarqube jacoco coveralls

# .NOTPARALLEL with targets needs at least gnumake 4.4.
# We get sporadic raise conditions on windows runner with 4.2.
# Let's configure it manual
# .NOTPARALLEL: coverage-throw.json coverage-exclude-throw.json
coverage-exclude-throw.json : | coverage-throw.json

main.gcda:
	./testcase

coverage-throw.json: main.gcda
	$(GCOVR) --gcov-keep --json-pretty --json $@

coverage-exclude-throw.json: main.gcda
	$(GCOVR) --gcov-keep --exclude-throw-branches --json-pretty --json $@

json: coverage-throw.json coverage-exclude-throw.json
	echo "Files created"

txt: coverage-throw.json coverage-exclude-throw.json
	$(GCOVR) -a coverage-throw.json -o coverage-throw.txt
	$(GCOVR) -a coverage-exclude-throw.json -o coverage-exclude-throw.txt

lcov: coverage-throw.json coverage-exclude-throw.json
	$(GCOVR) -a coverage-throw.json -o coverage-throw.lcov
	$(GCOVR) -a coverage-exclude-throw.json -o coverage-exclude-throw.lcov

cobertura: coverage-throw.json coverage-exclude-throw.json
	$(GCOVR) -x -a coverage-throw.json -o cobertura-throw.xml
	$(GCOVR) -x -a coverage-exclude-throw.json -o cobertura-exclude-throw.xml

html: coverage-throw.json coverage-exclude-throw.json
	$(GCOVR) --html-details -a coverage-throw.json -o coverage-throw.html
	$(GCOVR) --html-details -a coverage-exclude-throw.json -o coverage-exclude-throw.html

sonarqube: coverage-throw.json coverage-exclude-throw.json
	$(GCOVR) --sonarqube -a coverage-throw.json -o sonarqube-throw.xml
	$(GCOVR) --sonarqube -a coverage-exclude-throw.json -o sonarqube-exclude-throw.xml

jacoco: coverage-throw.json coverage-exclude-throw.json
	$(GCOVR) --jacoco -a coverage-throw.json -o jacoco-throw.xml
	$(GCOVR) --jacoco -a coverage-exclude-throw.json -o jacoco-exclude-throw.xml

coveralls: coverage-throw.json coverage-exclude-throw.json
	$(GCOVR) --coveralls-pretty --coveralls -a coverage-throw.json -o coveralls-throw.json
	$(GCOVR) --coveralls-pretty --coveralls -a coverage-exclude-throw.json -o coveralls-exclude-throw.json

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls-*.json
