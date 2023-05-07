
all:
	mkdir build
	cd build ; $(CXX) -fprofile-arcs -ftest-coverage -fPIC ../src/main.cpp -o testcase

run: json

json:
	cd build ; ./testcase
	chmod 0555 src
	$(GCOVR) --verbose --json-pretty --json coverage.json --gcov-ignore-errors=no_working_dir_found --root src build

clean:
	chmod 0755 src
	rm -rf build
	rm -f *.gc*
	rm -f coverage.json
