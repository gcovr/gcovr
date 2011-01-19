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

run: txt xml

txt:
	cd build && gcovrtest
	../../../scripts/gcovr -r . -d -o coverage.txt

xml:
	cd build && gcovrtest
	../../../scripts/gcovr -r . -d -x -o coverage.xml

clean:
	rm -rf build
	rm -f coverage.txt coverage.xml