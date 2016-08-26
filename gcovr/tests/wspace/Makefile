all:
	cd 'src code'; $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: txt xml html

txt:
	cd 'src code'; ./testcase
	../../../scripts/gcovr -r 'src code' -d -o coverage.txt

xml:
	cd 'src code'; ./testcase
	../../../scripts/gcovr -r 'src code' -d -x -o coverage.xml

html:
	cd 'src code'; ./testcase
	../../../scripts/gcovr -r 'src code' -d --html --html-details -o coverage.html

clean:
	rm -f */testcase
	rm -f */*.gc*
	rm -f coverage.txt coverage.xml coverage*.html
