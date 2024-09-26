all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: json txt lcov clover cobertura html sonarqube jacoco coveralls

coverage.json:
	./testcase
	$(GCOVR) -v --json-pretty --json $@ 2>stderr
	grep -F "4:7 without coverage information" stderr
# If block_ids entry is found the compiler supports the function excludes else we need to see a warning.
	grep -F ":11:20 $$(if grep -F '"block_ids"' --silent $@ ; then echo "is excluding branch 2 of line 5" ; else echo "needs at least gcc-14 with supported JSON format." ; fi)" stderr
	grep -F ":15:20 $$(if grep -F '"block_ids"' --silent $@ ; then echo "is excluding branch 4 of line 5" ; else echo "needs at least gcc-14 with supported JSON format." ; fi)" stderr
	grep -F ":19:39 $$(if grep -F '"block_ids"' --silent $@ ; then echo "found but no block ids defined at this line" ; else echo "needs at least gcc-14 with supported JSON format." ; fi)" stderr
	grep -F ":24:45 $$(if grep -F '"block_ids"' --silent $@ ; then echo "is excluding branch 5 of line 20" ; else echo "needs at least gcc-14 with supported JSON format." ; fi)" stderr

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
