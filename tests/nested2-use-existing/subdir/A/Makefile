
all:
	$(CXX) $(CXXFLAGS) -c file1.cpp -o file1.o
	$(CXX) $(CXXFLAGS) -c file2.cpp -o file2.o
	$(CXX) $(CXXFLAGS) -c file3.cpp -o file3.o
	$(CXX) $(CXXFLAGS) -c file4.cpp -o file4.o
	$(CXX) $(CXXFLAGS) -c file7.cpp -o file7.o
	make -C C CXXFLAGS="$(CXXFLAGS)"

coverage:
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file1.o
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file2.o
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file3.o
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file4.o
	$(GCOV) --branch-counts --branch-probabilities --preserve-paths file7.o
	make -C C coverage GCOV="$(GCOV)"
