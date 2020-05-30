CFLAGS=-fprofile-arcs -ftest-coverage
INSTALL ?= install -p

BASE_OS:=$(shell uname | cut -d'-' -f1)
ifeq ($(BASE_OS),Darwin)
  DYNLIB_EXT  = dylib
  CFLAGS     += -fPIC
  SOFLAGS    += -dynamiclib -undefined dynamic_lookup
endif
ifneq (,$(findstring MINGW,$(BASE_OS)))
  BASE_OS:=MSYS_NT
endif
ifeq ($(BASE_OS),CYGWIN_NT)
  DYNLIB_EXT = dll
  #DEFINES   += -mno-cygwin
  #SOFLAGS   += -shared -wl,--kill-at
  SOFLAGS    += -shared
endif
ifeq ($(BASE_OS),MSYS_NT)
  DYNLIB_EXT = dll
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
	$(CXX) $(CFLAGS) $(SOFLAGS) obj/libs.o -o lib/libs.$(DYNLIB_EXT)
	$(MAKE) -C testApp

run: txt xml html sonarqube

coverage.json:
ifeq ($(BASE_OS),MSYS_NT)
	PATH="`pwd`/lib:${PATH}" testApp/test/a.out
else
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
endif
	$(GCOVR) --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< -x -o coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

clean:
	rm -rf obj
	rm -f lib/*.$(DYNLIB_EXT)
	rm -f coverage*.* sonarqube*.*
	$(MAKE) -C testApp clean
