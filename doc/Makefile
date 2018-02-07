.PHONY: all outputs clean tests

PYTHON ?= python

%.html: %.rst outputs
	rst2html5.py --embed-stylesheet $< $@

all: guide.html

html: guide.html

outputs:
	../scripts/gcovr -h > examples/gcovr.out

tests:
	$(PYTHON) examples/test_examples.py -v

clean:
	rm -f `cat .gitignore`
