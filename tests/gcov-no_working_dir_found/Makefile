include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir build
	cd build ; $(CXX) $(CXXFLAGS) ../src/main.cpp -o testcase

run: json

json:
	cd build ; ./testcase
	chmod $(if $(filter Darwin,$(OSTYPE)),0455,0555) src build
	$(GCOVR) --verbose --json-pretty --json coverage.json $(if $(shell $(GCOV) --version 2>&1 | grep -F "JSON format version: 2"),,--gcov-ignore-errors=no_working_dir_found) --root src build

clean:
	chmod 0755 src build 2>/dev/null ; exit 0
	rm -rf build
	rm -f *.gc*
	rm -f coverage.json
