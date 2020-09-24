all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html-details --html-medium-threshold=100.0 --html-high-threshold=100.0 -o coverage.html

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q coverage*.html
	-cmd /C del /F /Q coverage.css
else
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
endif
