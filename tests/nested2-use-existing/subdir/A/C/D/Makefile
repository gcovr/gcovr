CFLAGS= -fprofile-arcs -ftest-coverage -fPIC

all:
	$(CXX) $(CFLAGS) -c file6.cpp -o file6.o

coverage:
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file6.o
