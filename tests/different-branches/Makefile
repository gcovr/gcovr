include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir -p build1 build2 build3 build4
	cd build1 ; $(CXX) $(CXXFLAGS) ../main.c -o testcase
	cd build2 ; $(CXX) $(CXXFLAGS) ../main.c -o testcase
	cd build3 ; $(CXX) $(CXXFLAGS) -DTWO_CONDITIONS ../main.c -o testcase
	cd build4 ; $(CXX) $(CXXFLAGS) -DTWO_CONDITIONS ../main.c -o testcase

run: json html

coverage.json:
	cd build1 ; ./testcase
	cd build2 ; ./testcase
	cd build3 ; ./testcase
	cd build4 ; ./testcase
	$(GCOVR) --verbose --gcov-keep --json-pretty --json coverage.json

json: coverage.json

html: coverage.json
	$(GCOVR) -a $< --html-self-contained --html-single-page --html-details coverage.html

clean:
	rm -rf build*
	rm -f *.gc* coverage*.*
