CFLAGS := -fPIC -fprofile-arcs -ftest-coverage -fprofile-abs-path

all: testcase

testcase: main.c
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f *.o
