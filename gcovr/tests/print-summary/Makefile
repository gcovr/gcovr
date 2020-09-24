CFLAGS = -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) main.cpp -o testcase

run: txt

GCOVR_TEST_OPTIONS = --print-summary

txt:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o coverage-output.txt > coverage.txt

clean:
ifeq ($(OS),Windows_NT)
	-cmd /C del /F /Q testcase*
	-cmd /C del /F /Q *.gc*
	-cmd /C del /F /Q *.o*
	-cmd /C del /F /Q coverage*.txt
else
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.txt
endif
