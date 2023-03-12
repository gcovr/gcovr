CFLAGS = -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) main.cpp -o testcase

run: txt

GCOVR_TEST_OPTIONS = --print-summary --calls --decision

txt:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o coverage-output.txt > coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.txt
