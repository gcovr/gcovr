include $(dir $(MAKEFILE_LIST))../common.mk
CFLAGS += -fprofile-abs-path

all:
	cd subfolder&& $(MAKE) CFLAGS="$(CFLAGS)"

run: json

json:
	cd subfolder&& ./testcase
	mv -f subfolder/*.gc?? ./
	$(GCOVR) -d --json-pretty --json coverage.json

clean:
	cd subfolder&& make clean
	rm -f testcase
	rm -f *.gc*
	rm -f coverage.json
