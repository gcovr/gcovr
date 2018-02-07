.PHONY: all outputs clean tests clean-images

PYTHON ?= python

SCREENSHOT_FROM_HTML = wkhtmltoimage --width 700

SCREENSHOTS = examples/example1.png examples/example2_example1_cpp.png

%.html: %.rst outputs
	rst2html5.py --embed-stylesheet $< $@

all: guide.html

html: guide.html

guide.html: $(SCREENSHOTS)

examples/example1.png:
	cd examples; ./example4.sh
	$(SCREENSHOT_FROM_HTML) examples/example1.html $@

examples/example2_example1_cpp.png:
	cd examples; ./example5.sh
	$(SCREENSHOT_FROM_HTML) examples/example1/example2.example1.cpp.html $@

outputs:
	../scripts/gcovr -h > examples/gcovr.out

tests:
	$(PYTHON) examples/test_examples.py -v

clean:
	rm -f `cat .gitignore`

clean-images:
	rm -f $(SCREENSHOTS)
