include $(dir $(MAKEFILE_LIST))../common.mk

all:
	$(CXX) $(CXXFLAGS) main.cpp -o testcase

run: html txt

html:
	./testcase
	rm -f *.toml
	cp config/pyproject.toml pyproject.toml
	$(GCOVR) ../

txt:
	./testcase
	rm -f *.toml
	sed -e 's/.*gcovr.*//' config/pyproject.toml > gcovr.toml
	$(GCOVR) --verbose ../

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.* *.toml
