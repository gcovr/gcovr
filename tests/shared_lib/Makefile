CFLAGS=-fprofile-arcs -ftest-coverage

BASE_OS:=$(shell uname | cut -d'-' -f1)
ifeq ($(BASE_OS),Darwin)
  DYNAMIC_LIB_EXT  = dylib
  CFLAGS     += -fPIC
  SHARED_OBJECT_FLAGS    += -dynamiclib -undefined dynamic_lookup
endif
ifeq ($(BASE_OS),CYGWIN_NT)
  DYNAMIC_LIB_EXT = dll
  #DEFINES   += -mno-cygwin
  #SHARED_OBJECT_FLAGS   += -shared -wl,--kill-at
  SHARED_OBJECT_FLAGS    += -shared
endif
ifneq ($(filter $(BASE_OS),MSYS_NT MINGW64_NT),)
  DYNAMIC_LIB_EXT = dll
  SHARED_OBJECT_FLAGS    += -shared
endif
ifeq ($(BASE_OS),Linux)
  DYNAMIC_LIB_EXT  = so
  CFLAGS     += -fPIC
  SHARED_OBJECT_FLAGS    += -shared
endif

ifndef DYNAMIC_LIB_EXT
  $(error ERROR: platform $(BASE_OS) not supported)
endif

all:
	mkdir obj
	$(CXX) $(CFLAGS) -c lib/lib.cpp -o obj/libs.o
	$(CXX) $(CFLAGS) $(SHARED_OBJECT_FLAGS) obj/libs.o -o lib/libs.$(DYNAMIC_LIB_EXT)
	$(MAKE) -C testApp

run: txt cobertura html sonarqube jacoco coveralls

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

cobertura: coverage.json
	$(GCOVR) -a $< --cobertura-pretty --cobertura cobertura.xml

html: coverage.json
	$(GCOVR) -a $< --html-details -o coverage.html

sonarqube: coverage.json
	$(GCOVR) -a $< --sonarqube sonarqube.xml

jacoco: coverage.json
	$(GCOVR) -a $< --jacoco jacoco.xml

coveralls: coverage.json
	$(GCOVR) -a $< --coveralls-pretty --coveralls coveralls.json

clean:
	rm -rf obj
	rm -f lib/*.$(DYNAMIC_LIB_EXT)
	rm -f coverage*.* cobertura*.* sonarqube*.* jacoco*.* coveralls.json
	$(MAKE) -C testApp clean
