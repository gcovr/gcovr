include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir build
	# Create the file with two additional lines
	(echo "" ; echo "" ; echo "" ; echo "" ; echo "" ; echo "" ; echo "" ; cat main.cpp) > build/main.cpp
	cd build; $(CXX) $(CXXFLAGS) main.cpp -o testcase
	cp -f main.cpp build/main.cpp

run: html

html:
	cd build; ./testcase
	cd build; $(GCOVR) -d --verbose --gcov-keep --html-details --html ../coverage.html 2>stderr || ( cat stderr & exit 1 )
	cd build; cat stderr
	cd build; grep -E "File .+main.cpp has [67] line\(s\) but coverage data has 10 line\(s\)\." stderr

clean:
	rm -rf build
	rm -f coverage*.html coverage.css
