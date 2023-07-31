
all:
	mkdir build
	cd build ; $(CXX) -fprofile-arcs -ftest-coverage -fPIC ../src/main.cpp -o testcase

run: json

json:
	cd build ; ./testcase
	chmod 0555 src build
	$(GCOVR) --verbose --json-pretty --json coverage.json --gcov-ignore-errors=output_error --root src build

clean:
	chmod 0755 src build 2>/dev/null ; exit 0
	rm -rf build
	rm -f *.gc*
	rm -f coverage.json
