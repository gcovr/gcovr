CFLAGS=-fprofile-arcs -ftest-coverage
INSTALL ?= install -p

BASE_OS:=$(shell uname | cut -d'-' -f1)
ifeq ($(BASE_OS),Darwin)
  DYNLIB_EXT  = dylib
  CFLAGS     += -fPIC
  SOFLAGS    += -dynamiclib -undefined dynamic_lookup
endif
ifeq ($(BASE_OS),CYGWIN_NT)
  DYNLIB_EXT = dll
  #DEFINES   += -mno-cygwin
  #SOFLAGS   += -shared -wl,--kill-at
  SOFLAGS    += -shared 
endif
ifeq ($(BASE_OS),Linux)
  DYNLIB_EXT  = so
  CFLAGS     += -fPIC 
  SOFLAGS    += -shared 
endif

ifndef DYNLIB_EXT
  $(error ERROR: platform $(BASE_OS) not supported)
endif

all:
	$(INSTALL) -d obj
	$(CXX) $(CFLAGS) -c lib/lib.cpp -o obj/libs.o
	$(CXX) $(CFLAGS) $(SOFLAGS) -shared obj/libs.o -o lib/libs.$(DYNLIB_EXT)
	$(MAKE) -C testApp

run: txt xml html

txt:
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
	../../../scripts/gcovr -d -o coverage.txt

xml:
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
	../../../scripts/gcovr -d -x -o coverage.xml

html:
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
	../../../scripts/gcovr -d --html --html-details -o coverage.html

clean:
	rm -rf obj
	rm -f lib/*.so
	rm -f coverage.xml coverage.txt coverage*.html
	$(MAKE) -C testApp clean
