include $(dir $(MAKEFILE_LIST))../../common.mk

all: subfolder/testcase

subfolder/testcase:subfolder/main.o subfolder/lib.o
	$(CXX) $(CXXFLAGS) -o $@ $^

.cpp.o:
	$(CXX) $(CXXFLAGS) -c -I../include -o $@ $^

clean:
	rm -f subfolder/testcase
	rm -f subfolder/*.gc*
	rm -f subfolder/*.o
