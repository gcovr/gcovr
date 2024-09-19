include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt

GCOVR_TEST_OPTIONS = --txt-summary

txt:
	./testcase
	$(GCOVR) $(GCOVR_TEST_OPTIONS) -d -o coverage-output.txt > coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.txt
