CFLAGS=-fprofile-arcs -ftest-coverage

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
	g++ $(CFLAGS) -c lib/lib.cpp -o obj/libs.o
	g++ $(CFLAGS) $(SOFLAGS) -shared obj/libs.o -o lib/libs.$(DYNLIB_EXT)
	cd testApp && $(MAKE)

run: txt xml

xml:
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
	../../../scripts/gcovr -r . -v -d -x -o coverage.xml

txt:
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
	../../../scripts/gcovr -r . -d -o coverage.txt

clean:
	rm -rf obj/*
	rm -f lib/*.so
	rm -rf testApp/test/*
	rm -f testApp/*.gc*
	rm -f coverage.xml coverage.txt
