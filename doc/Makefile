.PHONY: all anchors outputs clean tests

PYTHON ?= python

%.html: %.txt anchors outputs
	asciidoc -a data-uri -v -b html -d article -n -a toc2 -a icons $<

all: guide.html

html: guide.html

anchors: guide.txt
	$(PYTHON) include_anchors.py $<

outputs:
	../scripts/gcovr -h > examples/gcovr.out

tests:
	$(PYTHON) examples/test_examples.py -v

clean:
	rm -f `cat .gitignore`
