all:
	g++ -fprofile-arcs -ftest-coverage -fPIC -c lib/lib.cpp -o obj/libs.o
	g++ -fprofile-arcs -ftest-coverage -fPIC -shared obj/libs.o -o lib/libs.so
	cd testApp && make

run:
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
	../../../scripts/gcovr -r . -v -d -x -o coverage.xml
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
	../../../scripts/gcovr -r . -d -o coverage.txt

clean:
	rm -rf obj/*
	rm -f lib/*.so
	rm -rf testApp/test/*
	rm -f testApp/*.gc*
	rm -f coverage.xml coverage.txt
