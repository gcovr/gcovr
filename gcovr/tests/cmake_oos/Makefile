# Original build.sh script from ticket:
#   rm -fr build
#   mkdir build
#   cd build
#   cmake ..
#   make
#   gcovrtest

all:
	mkdir -p build
	cd build && cmake .. && make
	#cd build && cmake --debug-output --trace -Wdev --debug-trycompile .. && make

run: txt xml html

txt:
	cd build && ./gcovrtest
	../../../scripts/gcovr -r . -d -o coverage.txt

xml:
	cd build && ./gcovrtest
	../../../scripts/gcovr -r . -d -x -o coverage.xml

html:
	cd build && ./gcovrtest
	../../../scripts/gcovr -r . -d --html --html-details -o coverage.html

clean:
	rm -rf build
	rm -f coverage.txt coverage.xml coverage*.html

