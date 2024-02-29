all:
	echo "Nothing to build"

run: json

json:
	cp main.case_1 main.case_1.gcov
	mkdir -p data
	cp main.case_2 data/main.case_2.gcov
	$(GCOVR) --verbose --gcov-keep --gcov-use-existing-files --json-pretty --json coverage.json main.case_1.gcov data

clean:
	rm -f *.gcov
	rm -f coveralls.json
