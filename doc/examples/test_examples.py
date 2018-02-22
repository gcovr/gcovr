import glob
import os
import pytest
import subprocess
import sys

from gcovr.tests.test_gcovr import SCRUBBERS, ASSERT_EQUALS

datadir = os.path.dirname(os.path.abspath(__file__))


def find_test_cases():
    if sys.platform.startswith('win'):
        return
    for script in glob.glob('{}/*.sh'.format(datadir)):
        basename = os.path.basename(script)
        name, _ = os.path.splitext(basename)
        for ext in 'txt xml'.split():
            baseline = '{}/{}.{}'.format(datadir, name, ext)
            if not os.path.exists(baseline):
                continue
            yield (name, script, baseline)


@pytest.mark.parametrize(
    'args', find_test_cases(),
    ids=lambda args: os.path.basename(args[2]))
def test_example(args):
    name, cmd, baseline_file = args
    ext = os.path.splitext(baseline_file)[1][1:]
    scrub = SCRUBBERS[ext]
    assert_equals = ASSERT_EQUALS.get(ext, None)

    startdir = os.getcwd()
    os.chdir(datadir)
    output = scrub(subprocess.check_output(cmd).decode())
    with open(baseline_file) as f:
        baseline = scrub(f.read())
    if assert_equals is not None:
        assert_equals(output, baseline)
    else:
        assert output == baseline
    os.chdir(startdir)
