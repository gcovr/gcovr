include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html-details --html-high-threshold=75.0 --html-medium-threshold-branch=74 \
		--html-medium-threshold-line=70 --html-high-threshold-line=70 -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
