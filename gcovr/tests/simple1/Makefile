ifeq ($(OS),Windows_NT)
	SHELL=cmd
endif

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json json_summary coveralls

txt:
	./testcase
ifeq ($(OS),Windows_NT)
	$(GCOVR) --fail-under-line 80.1 && echo errorlevel
else
	# a couple of tests about failure thresholds
	$(GCOVR) --fail-under-line 80.1; test $$? -eq 2
	$(GCOVR) --fail-under-branch 50.1; test $$? -eq 4
	$(GCOVR) --fail-under-line 80.1 --fail-under-branch 50.1; test $$? -eq 6
	$(GCOVR) --fail-under-line 79.9 --fail-under-branch 49.9
	# generate actual output
endif
	$(GCOVR) -d --txt -o coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x -o coverage.xml

html:
	./testcase
ifneq ($(OS),Windows_NT)
	# these test cases also cover some CSS-linking permutations
endif
	$(GCOVR) --html coverage-summary-includecss.html
	$(GCOVR) --html coverage-summary-linkcss.html --no-html-self-contained
	$(GCOVR) --html-details coverage-details-includecss.html --html-self-contained
	$(GCOVR) --html-details coverage-details-linkcss.html

sonarqube:
	./testcase
	$(GCOVR) -d --sonarqube sonarqube.xml


json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty -o summary_coverage.json

json:
	./testcase
	$(GCOVR) --json coverage.json
	
coveralls:
	./testcase
	$(GCOVR) -d --coveralls coveralls.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q coverage.txt
	-cmd /C del /F /Q coverage.xml
	-cmd /C del /F /Q coverage*.html
	-cmd /C del /F /Q coverage*.css
	-cmd /C del /F /Q sonarqube.xml
	-cmd /C del /F /Q coverage.json
	-cmd /C del /F /Q summary_coverage.json
	-cmd /C del /F /Q coveralls.json
else
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage*.css sonarqube.xml coverage.json summary_coverage.json coveralls.json
endif

