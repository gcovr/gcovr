all:
	g++ -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml

txt:
	./testcase
	../../../scripts/gcovr -f '.*/tests/' -d -o coverage.txt

xml:
	./testcase
	../../../scripts/gcovr -f '.*/tests/' -d -x -o coverage.xml

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.txt coverage.xml