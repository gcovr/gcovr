include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) --html --html-self-contained --config config/gcovr.error.config 2>&1 | grep -F "gcovr.error.config: 1: gcov-ignore-parse-errors: must be one of"
	$(GCOVR) --html --html-self-contained --config config/gcovr.txt-branch.config 2>&1 | grep -F "(WARNING) Deprecated config key txt-branch used, please use 'txt-metric=branch' instead."
	$(GCOVR) --html --html-self-contained --config config/gcovr.config

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
