include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html

html:
	./testcase
	$(GCOVR) --html-details --html-block-ids --html-theme github.green -o coverage.green.html
	$(GCOVR) --html-details --html-block-ids --html-theme github.blue -o coverage.blue.html
	$(GCOVR) --html-details --html-block-ids --html-theme github.dark-green -o coverage.dark-green.html
	$(GCOVR) --html-details --html-block-ids --html-theme github.dark-blue -o coverage.dark-blue.html
	$(GCOVR) --html-details --html-block-ids --html-theme github.green -o coverage.calls.html --calls
	$(GCOVR) --html-details --html-block-ids --html-theme github.green -o coverage.decisions.html --decisions
	$(GCOVR) --html-details --html-block-ids --html-theme github.green -o coverage.call_decisions.html --decisions --calls
	$(GCOVR) --html-details --html-block-ids --html-theme github.green -o coverage.legend.html --high-threshold-branch 85 --high-threshold-line 76

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.html coverage*.css
