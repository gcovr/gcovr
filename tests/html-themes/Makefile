include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) --html-details --html-theme green -o coverage.green.html
	$(GCOVR) --html-details --html-theme blue -o coverage.blue.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage*.css
