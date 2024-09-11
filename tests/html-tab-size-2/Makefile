include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html --no-html-self-contained --html-tab-size=2 -o coverage.html

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
