all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase


run: txt xml html json json_summary coveralls

txt:
	./testcase
	$(GCOVR) -d --txt > coverage.txt

xml:
	./testcase
	$(GCOVR) -d -x > coverage.xml

html:
	./testcase
	$(GCOVR) -d --html > coverage.html

json:
	./testcase
	$(GCOVR) --json > coverage.json

json_summary:
	./testcase
	$(GCOVR) -d --json-summary-pretty > summary_coverage.json

coveralls:
	./testcase
	$(GCOVR) -d --coveralls > coveralls.json

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q coverage.txt
	-cmd /C del /F /Q coverage.xml
	-cmd /C del /F /Q coverage*.html
	-cmd /C del /F /Q coverage.json
	-cmd /C del /F /Q summary_coverage.json
	-cmd /C del /F /Q coveralls.json
else
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml coverage*.html coverage.json summary_coverage.json coveralls.json
endif

