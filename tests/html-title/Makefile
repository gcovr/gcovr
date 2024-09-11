include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

# Use $$(...) to run the ls command in the shell.
# The $(shell ...) doesn't work here because it's evaluated before running the executable
html:
	./testcase
	$(GCOVR) -d --verbose --html-details --html-title="Title of report" -o coverage.html $$(ls *.gcda)

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage.css
