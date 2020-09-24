all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: html txt

html:
	./testcase
	$(GCOVR) -d --html-details coverage.html

txt:
	./testcase
	$(GCOVR) -d --output coverage.txt

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q coverage*.txt
	-cmd /C del /F /Q coverage*.html
	-cmd /C del /F /Q coverage*.css
else
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage*.css
endif
