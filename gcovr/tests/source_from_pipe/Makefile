
all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC -c code.cpp -o code.o
	cat test.cpp | $(CXX) -fprofile-arcs -ftest-coverage -fPIC -x c++ -c - -o test.o
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC code.o test.o -o testcase

run: txt cobertura html sonarqube coveralls

coverage.json:
	./testcase
	$(GCOVR) --gcov-keep --verbose --gcov-ignore-errors no_working_dir_found --json-pretty --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

coveralls: coverage.json
	$(GCOVR) -a $<  --coveralls-pretty --coveralls coveralls.json

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

clean:
	rm -rf build
	rm -f coverage*.* cobertura*.* sonarqube*.* coveralls.json
