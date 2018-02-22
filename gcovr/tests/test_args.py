from ..__main__ import main
from ..version import __version__


# The CaptureObject class holds the capture method result
class CaptureObject:
    def __init__(self, out, err, exception):
        self.out = out
        self.err = err
        self.exception = exception


# The capture method calls the main method and captures its output/error
# streams and exit code
def capture(capsys, args):
    e = None
    try:
        main(args)
    except SystemExit as exception:
        e = exception
    out, err = capsys.readouterr()
    return CaptureObject(out, err, e)


def test_version(capsys):
    c = capture(capsys, ['--version'])
    assert c.err == ''
    assert c.out.startswith('gcovr %s' % __version__)
    assert c.exception.code == 0


def test_help(capsys):
    c = capture(capsys, ['-h'])
    assert c.err == ''
    assert c.out.startswith('Usage: gcovr [options]')
    assert c.exception.code == 0


def test_empty_root(capsys):
    c = capture(capsys, ['-r', ''])
    assert c.out == ''
    assert c.err.startswith('(ERROR) empty --root option.')
    assert c.exception.code == 1


def test_empty_objdir(capsys):
    c = capture(capsys, ['--object-directory', ''])
    assert c.out == ''
    assert c.err.startswith(
        '(ERROR) empty --object-directory option.')
    assert c.exception.code == 1


def test_invalid_objdir(capsys):
    c = capture(capsys, ['--object-directory', 'not-existing-dir'])
    assert c.out == ''
    assert c.err.startswith(
        '(ERROR) Bad --object-directory option.')
    assert c.exception.code == 1


def test_branch_threshold_nan(capsys):
    c = capture(capsys, ['--fail-under-branch', 'nan'])
    assert c.out == ''
    assert 'not in range [0.0, 100.0]' in c.err
    assert c.exception.code != 0


def test_line_threshold_negative(capsys):
    c = capture(capsys, ['--fail-under-line', '-0.1'])
    assert c.out == ''
    assert 'not in range [0.0, 100.0]' in c.err
    assert c.exception.code != 0


def test_line_threshold_100_1(capsys):
    c = capture(capsys, ['--fail-under-line', '100.1'])
    assert c.out == ''
    assert 'not in range [0.0, 100.0]' in c.err
    assert c.exception.code != 0
