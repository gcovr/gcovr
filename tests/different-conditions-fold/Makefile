include $(dir $(MAKEFILE_LIST))../common.mk

all:
	python3 ../create_gz.py conditions-1.json conditions-1.gcov.json.gz
	python3 ../create_gz.py conditions-2.json conditions-2.gcov.json.gz

run: json

json:
	$(GCOVR) --gcov-use-existing --verbose --merge-mode-conditions=fold --json-pretty --json coverage.json

clean:
	rm -f *.gcov.json.gz coverage.json
