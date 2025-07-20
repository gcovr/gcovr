include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: txt

txt:
	./testcase
	$(GCOVR) --gcov-executable $$PWD/gcov-stub --txt coverage.txt 2>stderr ; test $$? -eq 64 || (cat stderr && exit 1)
	cat stderr
	grep "AssertionError: Sanity check failed, output file .*/does#not#exist.gcov doesn't exist but no error from GCOV detected." stderr
	if [ "$$GITHUB_ACTIONS" != "" ] ; then grep -F "::error::(ERROR) Traceback (most recent call last):" stderr ; fi
	grep -F "RuntimeError: Worker thread raised exception, workers canceled." stderr
	if [ "$$GITHUB_ACTIONS" != "" ] ; then grep -F "::error::(ERROR) Error occurred while reading reports:" stderr ; fi

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.txt
