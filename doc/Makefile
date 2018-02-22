.PHONY: all outputs clean tests clean-images

PYTHON ?= python

SCREENSHOT_FROM_HTML = wkhtmltoimage --width 700 --quality 5

SCREENSHOTS = screenshot-html.png screenshot-html-details.example.cpp.png

%.html: %.rst outputs
	rst2html5.py --embed-stylesheet $< $@

all: guide.html

html: guide.html

guide.html: $(SCREENSHOTS)

screenshot-%.png: examples/example-%.html
	$(SCREENSHOT_FROM_HTML) $< $@

examples/example-%.html:
	cd examples; ./example_html.sh

outputs:
	../scripts/gcovr -h > examples/gcovr.out

tests:
	$(PYTHON) -m pytest examples -v

clean:
	rm -f `cat .gitignore`

clean-images:
	rm -f $(SCREENSHOTS)
