include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html txt

html:
	./testcase
	$(GCOVR) -d --html-details coverage.html

txt:
	./testcase
	$(GCOVR) -d --output coverage.txt

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage*.html coverage*.css
