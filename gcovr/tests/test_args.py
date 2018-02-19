import sys
import unittest

from ..__main__ import main
from ..version import __version__


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


# The CaptureObject class holds the capture method result
class CaptureObject:
    def __init__(self, out, err, exception):
        self.out = out
        self.err = err
        self.exception = exception


# The StringIOBuffered class is used by the capture method to capture stdout
# and stderr content even if they are closed by the main method
class StringIOBuffered(StringIO):
    def __init__(self):
        self._data = None
        StringIO.__init__(self)

    def data(self):
        self.close()
        return self._data

    def close(self):
        try:
            if self._data is None:
                self.seek(0)
                self._data = self.read()
        finally:
            StringIO.close(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# The capture method calls the main method and captures its output/error
# streams and exit code
def capture(args):
    with StringIOBuffered() as newout, StringIOBuffered() as newerr:
        err, sys.stderr = sys.stderr, newerr
        out, sys.stdout = sys.stdout, newout
        try:
            try:
                e = None
                main(args)
            except SystemExit as exception:
                e = exception
            return CaptureObject(newout.data(), newerr.data(), e)
        finally:
            sys.stderr = err
            sys.stdout = out


class TestArgs(unittest.TestCase):

    def test_version(self):
        c = capture(['--version'])
        self.assertEqual(c.err, '')
        self.assertTrue(c.out.startswith('gcovr %s' % __version__))
        self.assertEqual(c.exception.code, 0)

    def test_help(self):
        c = capture(['-h'])
        self.assertEqual(c.err, '')
        self.assertTrue(c.out.startswith('Usage: gcovr [options]'))
        self.assertEqual(c.exception.code, 0)

    def test_empty_root(self):
        c = capture(['-r', ''])
        self.assertEqual(c.out, '')
        self.assertTrue(c.err.startswith('(ERROR) empty --root option.'))
        self.assertEqual(c.exception.code, 1)

    def test_empty_objdir(self):
        c = capture(['--object-directory', ''])
        self.assertEqual(c.out, '')
        self.assertTrue(c.err.startswith(
            '(ERROR) empty --object-directory option.'))
        self.assertEqual(c.exception.code, 1)

    def test_invalid_objdir(self):
        c = capture(['--object-directory', 'not-existing-dir'])
        self.assertEqual(c.out, '')
        self.assertTrue(c.err.startswith(
            '(ERROR) Bad --object-directory option.'))
        self.assertEqual(c.exception.code, 1)

    def test_branch_threshold_nan(self):
        c = capture(['--fail-under-branch', 'nan'])
        self.assertEqual(c.out, '')
        self.assertTrue('not in range [0.0, 100.0]' in c.err)
        self.assertNotEqual(c.exception.code, 0)

    def test_line_threshold_negative(self):
        c = capture(['--fail-under-line', '-0.1'])
        self.assertEqual(c.out, '')
        self.assertTrue('not in range [0.0, 100.0]' in c.err)
        self.assertNotEqual(c.exception.code, 0)

    def test_line_threshold_100_1(self):
        c = capture(['--fail-under-line', '100.1'])
        self.assertEqual(c.out, '')
        self.assertTrue('not in range [0.0, 100.0]' in c.err)
        self.assertNotEqual(c.exception.code, 0)
