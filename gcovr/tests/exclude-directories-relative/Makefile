CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
ifeq ($(OS),Windows_NT)
	-mkdir build\a
	-mkdir build\b
else
	mkdir -p build/a build/b
endif
	$(CXX) $(CFLAGS) -c a/file1.cpp -o build/a/file1.o
	$(CXX) $(CFLAGS) -c b/main.cpp -o build/b/main.o
	$(CXX) $(CFLAGS) build/b/main.o build/a/file1.o -o testcase

run: txt xml html sonarqube coveralls

coverage.json:
	./testcase
	$(GCOVR) --exclude-directories 'build/a' --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls coveralls.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q /S build
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube*.*
	-cmd /C del /F /Q coveralls.json
else
	rm -f testcase
	rm -rf build  # remove *.gc* *.o
	rm -f coverage*.* sonarqube*.* coveralls.json
endif
