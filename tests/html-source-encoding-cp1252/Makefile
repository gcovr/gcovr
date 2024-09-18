include $(dir $(MAKEFILE_LIST))../common.mk

# cspell:ignore finput
all:
	$(CXX) $(CXXFLAGS) -finput-charset=cp1252 main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) -d --html-details -o coverage.html --source-encoding cp1252

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
