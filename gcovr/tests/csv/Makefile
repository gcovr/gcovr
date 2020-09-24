all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: csv

csv:
	./testcase
	$(GCOVR) -d --csv -o coverage.csv

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q coverage.csv
else
	rm -f testcase
	rm -f *.gc* coverage.csv
endif