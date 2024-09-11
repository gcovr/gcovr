include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html-details --html-medium-threshold=100.0 --html-high-threshold=100.0 -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
