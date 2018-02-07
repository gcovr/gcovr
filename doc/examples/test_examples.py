# Imports
import pyutilib.th as unittest
import glob
import os
from os.path import dirname, abspath, basename
import sys
import re

currdir = dirname(abspath(__file__)) + os.sep
datadir = currdir

compilerre = re.compile("^(?P<path>[^:]+)(?P<rest>:.*)$")
dirre = re.compile("^([^%s]*/)*" % re.escape(os.sep))
xmlre = re.compile("\"(?P<path>[^\"]*/[^\"]*)\"")
datere = re.compile("date=\"[^\"]*\"")
versionre = re.compile("version=\"[^\"]*\"")
timestampre = re.compile("timestamp=\"[^\"]*\"")
failure = re.compile("^(?P<prefix>.+)file=\"(?P<path>[^\"]+)\"(?P<suffix>.*)$")


def filter(line):
    # for xml, remove prefixes from everything that looks like a
    # file path inside ""
    line = xmlre.sub(
        lambda match: '"' + re.sub("^[^/]+/", "", match.group(1)) + '"',
        line
    )
    # Remove date info
    line = datere.sub(lambda match: 'date=""', line)
    # Remove version info
    line = versionre.sub(lambda match: 'version=""', line)
    # Remove timestamp info
    line = timestampre.sub(lambda match: 'timestamp=""', line)

    if 'Running' in line:
        return False
    if "IGNORE" in line:
        return True
    pathmatch = compilerre.match(line)  # see if we can remove the basedir
    failmatch = failure.match(line)  # see if we can remove the basedir
    # print "HERE", pathmatch, failmatch
    if failmatch:
        parts = failmatch.groupdict()
        # print "X", parts
        line = "%s file=\"%s\" %s" % (parts['prefix'], dirre.sub("", parts['path']), parts['suffix'])
    elif pathmatch:
        parts = pathmatch.groupdict()
        # print "Y", parts
        line = dirre.sub("", parts['path']) + parts['rest']
    return line


# Declare an empty TestCase class
class Test(unittest.TestCase):
    pass


if not sys.platform.startswith('win'):
    # Find all *.sh files, and use them to define baseline tests
    for script in glob.glob(datadir + '*.sh'):
        bname = basename(script)
        name = bname.split('.')[0]
        for extension in '.txt .xml'.split():
            baseline = datadir + name + extension
            if os.path.exists(baseline):
                Test.add_baseline_test(
                    cwd=datadir, cmd=script, name=name,
                    baseline=baseline, filter=filter)

# Execute the tests
if __name__ == '__main__':
    unittest.main()
