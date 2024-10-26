include $(dir $(MAKEFILE_LIST))../common.mk

all:
	python3 ../create_gz.py conditions-2.json conditions-2.gcov.json.gz
	python3 ../create_gz.py conditions-4.json conditions-4.gcov.json.gz

run: json

json:
	$(GCOVR) --gcov-use-existing --verbose --json-pretty --json > coverage.log 2>&1; test $$? -eq 64 || (cat coverage.log && exit 1)
	grep -E 'The number of conditions must be equal, got 4 and expected 2 while merging .*/main\.c:4' coverage.log

clean:
	rm -f coverage.log *.gcov.json.gz
