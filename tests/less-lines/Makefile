all:
	mkdir build
	# Create the file with two additional lines
	(echo "" ; echo "" ; echo "" ; echo "" ; echo "" ; echo "" ; echo "" ; cat main.cpp) > build/main.cpp
	cd build; $(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase
	cp -f main.cpp build/main.cpp

run: html

html:
	cd build; ./testcase
	cd build; $(GCOVR) -d --verbose --gcov-keep --html-details --html ../coverage.html 2>stderr || ( cat stderr & exit 1 )
	cd build; grep -P "File .+main.cpp has [67] line\(s\) but coverage data has 10 line\(s\)\." stderr || ( cat stderr & exit 1 )

clean:
	rm -rf build
	rm -f coverage*.html coverage.css
