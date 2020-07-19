from ..__main__ import main
from ..version import __version__
import re
import sys


# The CaptureObject class holds the capture method result
class CaptureObject:
    def __init__(self, out, err, exception):
        self.out = out
        self.err = err
        self.exception = exception


# The capture method calls the main method and captures its output/error
# streams and exit code
def capture(capsys, args, other_ex=()):
    e = None
    try:
        main(args)
        # Explicit SystemExit exception in case main() returns normally
        sys.exit(0)
    except SystemExit as exception:
        e = exception
    except other_ex as exception:
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
    assert c.out.startswith('usage: gcovr [options]')
    assert c.exception.code == 0


def test_empty_root(capsys):
    c = capture(capsys, ['-r', ''])
    assert c.out == ''
    assert c.err.startswith('(ERROR) empty --root option.')
    assert c.exception.code == 1


def test_empty_exclude(capsys):
    c = capture(capsys, ['--exclude', ''])
    assert c.out == ''
    assert 'filter cannot be empty' in c.err
    assert c.exception.code != 0


def test_empty_exclude_directories(capsys):
    c = capture(capsys, ['--exclude-directories', ''])
    assert c.out == ''
    assert 'filter cannot be empty' in c.err
    assert c.exception.code != 0


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


def helper_test_non_existing_directory_output(capsys, option='--output'):
    c = capture(capsys, [option, 'not-existing-dir/file.txt'])
    assert c.out == ''
    assert 'Could not create output file \'not-existing-dir/file.txt\': ' in c.err
    assert c.exception.code != 0


def test_non_existing_directory_xml(capsys):
    helper_test_non_existing_directory_output(capsys, '--xml')


def test_non_existing_directory_html(capsys):
    helper_test_non_existing_directory_output(capsys, '--html')


def test_non_existing_directory_html_details(capsys):
    helper_test_non_existing_directory_output(capsys, '--html-details')


def test_non_existing_directory_sonarqube(capsys):
    helper_test_non_existing_directory_output(capsys, '--sonarqube')


def test_non_existing_directory_json(capsys):
    helper_test_non_existing_directory_output(capsys, '--json')


def test_non_existing_directory_csv(capsys):
    helper_test_non_existing_directory_output(capsys, '--csv')


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


def test_filter_backslashes_are_detected(capsys):
    # gcov-exclude all to prevent any coverage data from being found
    c = capture(
        capsys,
        args=['--filter', r'C:\\foo\moo', '--gcov-exclude', ''],
        other_ex=re.error)
    assert c.err.startswith(
        '(WARNING) filters must use forward slashes as path separators\n'
        '(WARNING) your filter : C:\\\\foo\\moo\n'
        '(WARNING) did you mean: C:/foo/moo\n')
    assert isinstance(c.exception, re.error) or c.exception.code == 0


def test_html_css_not_exists(capsys):
    c = capture(capsys, ['--html-css', '/File/does/not/\texist'])
    assert c.out == ''
    assert 'Should be a file that already exists: \'/File/does/not/\\texist\'' in c.err
    assert c.exception.code != 0


def test_html_title_empty_string(capsys):
    c = capture(capsys, ['--html-title', ''])
    assert c.out == ''
    assert 'an empty --html_title= is not allowed.' in c.err
    assert c.exception.code != 0


def test_html_medium_threshold_nan(capsys):
    c = capture(capsys, ['--html-medium-threshold', 'nan'])
    assert c.out == ''
    assert 'not in range [0.0, 100.0]' in c.err
    assert c.exception.code != 0


def test_html_medium_threshold_negative(capsys):
    c = capture(capsys, ['--html-medium-threshold', '-0.1'])
    assert c.out == ''
    assert 'not in range [0.0, 100.0]' in c.err
    assert c.exception.code != 0


def test_html_medium_threshold_zero(capsys):
    c = capture(capsys, ['--html-medium-threshold', '0.0'])
    assert c.out == ''
    assert 'value of --html-medium-threshold= should not be zero.' in c.err
    assert c.exception.code != 0


def test_html_high_threshold_nan(capsys):
    c = capture(capsys, ['--html-high-threshold', 'nan'])
    assert c.out == ''
    assert 'not in range [0.0, 100.0]' in c.err
    assert c.exception.code != 0


def test_html_high_threshold_negative(capsys):
    c = capture(capsys, ['--html-high-threshold', '-0.1'])
    assert c.out == ''
    assert 'not in range [0.0, 100.0]' in c.err
    assert c.exception.code != 0


def test_html_medium_threshold_gt_html_high_threshold(capsys):
    c = capture(capsys, ['--html-medium-threshold', '60', '--html-high-threshold', '50'])
    assert c.out == ''
    assert 'value of --html-medium-threshold=60.0 should be\nlower than or equal to the value of --html-high-threshold=50.0.' in c.err
    assert c.exception.code != 0


def test_html_tab_size_zero(capsys):
    c = capture(capsys, ['--html-tab-size', '0'])
    assert c.out == ''
    assert 'value of --html-tab-size= should be greater 0.' in c.err
    assert c.exception.code != 0


def test_multiple_output_formats_to_stdout(capsys):
    c = capture(capsys, ['--xml', '--html', '--sonarqube'])
    assert 'HTML output skipped' in c.err
    assert 'Sonarqube output skipped' in c.err
    assert c.exception.code == 0


def test_no_self_contained_without_file(capsys):
    c = capture(capsys, ['--no-html-self-contained', '--html'])
    assert c.out == ''
    assert 'can only disable --html-self-contained when a named output is given' in c.err
    assert c.exception.code != 0


def test_html_injection_via_json(capsys, tmp_path):
    import json
    import markupsafe

    script = '<script>alert("pwned")</script>'
    jsondata = {
        'gcovr/format_version': 0.1,
        'files': [
            {'file': script, 'lines': []},
            {'file': 'other', 'lines': []},
        ],
    }

    tempfile = tmp_path / 'injection.json'

    with tempfile.open('w+') as jsonfile:
        json.dump(jsondata, jsonfile)

    c = capture(capsys, ['-a', str(tempfile), '--html'])

    assert script not in c.out
    assert str(markupsafe.escape(script)) in c.out, '--- got:\n{}\n---'.format(c.out)
    assert c.exception.code == 0


def test_exclude_lines_by_pattern(capsys):
    c = capture(capsys, ['--exclude-lines-by-pattern', 'example.**'])
    assert 'Invalid regular expression' in c.err
    assert c.exception.code != 0
