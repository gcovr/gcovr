CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	mkdir -p build/a build/b
	$(CXX) $(CFLAGS) -c a/file1.cpp -o build/a/file1.o
	$(CXX) $(CFLAGS) -c b/main.cpp -o build/b/main.o
	$(CXX) $(CFLAGS) build/b/main.o build/a/file1.o -o testcase

run: txt cobertura html sonarqube coveralls

coverage.json:
	./testcase
	$(GCOVR) --exclude-directories 'build/a' --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -f testcase
	rm -rf build  # remove *.gc* *.o
	rm -f coverage*.* cobertura*.* sonarqube*.* coveralls.json
