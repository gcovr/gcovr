all:
ifeq ($(OS),Windows_NT)
	mkdir output
	cd output && $(CXX) -fprofile-arcs -ftest-coverage -fPIC ../main.cpp -o testcase
else
	mkdir -p output && cd output && $(CXX) -fprofile-arcs -ftest-coverage -fPIC ../main.cpp -o testcase
endif

run: txt xml html sonarqube coveralls

coverage.json:
	./output/testcase
	$(GCOVR) --json coverage.json

txt: coverage.json
	$(GCOVR) -o coverage.txt

xml: coverage.json
	$(GCOVR) -x -o coverage.xml

html: coverage.json
	$(GCOVR) --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) --coveralls coveralls.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C rmdir /S /Q output
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube*.*
	-cmd /C del /F /Q coveralls.json
else
	rm -rf output
	rm -f coverage*.* sonarqube*.* coveralls.json
endif
