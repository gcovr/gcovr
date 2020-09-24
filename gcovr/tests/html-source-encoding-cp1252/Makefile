all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC --encoding cp1252 main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html --source-encoding cp1252

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
