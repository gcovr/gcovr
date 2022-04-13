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
ifneq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
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
	mkdir obj
	$(CXX) $(CFLAGS) -c lib/lib.cpp -o obj/libs.o
	$(CXX) $(CFLAGS) $(SOFLAGS) obj/libs.o -o lib/libs.$(DYNLIB_EXT)
	$(MAKE) -C testApp

run: txt xml html sonarqube coveralls

ifneq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
ifneq ($(notdir $(SHELL)),sh)
coverage.json : export PATH := $(subst /,\,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))\lib;${PATH}
endif
endif

coverage.json:
ifeq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
	LD_LIBRARY_PATH=`pwd`/lib testApp/test/a.out
else
ifeq ($(notdir $(SHELL)),sh)
	PATH="`pwd`/lib:${PATH}" testApp/test/a.out
else
	testApp/test/a.out
endif
endif
	$(GCOVR) --json-pretty --json $@

txt: coverage.json
	$(GCOVR) -a $< -o coverage.txt

xml: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura coverage.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -rf obj
	rm -f lib/*.$(DYNLIB_EXT)
	rm -f coverage*.* sonarqube*.* coveralls.json
	$(MAKE) -C testApp clean
