all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html sonarqube json_summary coveralls

coverage.json:
	./testcase
	$(GCOVR) --json coverage.json

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube -o sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls coveralls.json

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty -o summary_coverage.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q *.o*
	-cmd /C del /F /Q coverage*.*
	-cmd /C del /F /Q sonarqube*.*
	-cmd /C del /F /Q summary_coverage.json
	-cmd /C del /F /Q coveralls.json
else
	rm -f testcase
	rm -f *.gc*
	rm -f *.o
	rm -f coverage*.* sonarqube*.* summary_coverage.json coveralls.json
endif
