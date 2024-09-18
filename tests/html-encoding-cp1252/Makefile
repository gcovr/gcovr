include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html --source-encoding utf8 --html-encoding cp1252

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage*.css
