#!/usr/bin/env python
import os
import re
import sys
import subprocess
import traceback
import pyutilib.th as unittest

basedir = os.path.split(os.path.abspath(__file__))[0]
starting_dir = os.getcwd()

class GcovrTxt(unittest.TestCase):
    def __init__(self, *args, **kwds):
        unittest.TestCase.__init__(self, *args, **kwds)

GcovrTxt = unittest.category('smoke')(GcovrTxt)


class GcovrXml(unittest.TestCase):
    def __init__(self, *args, **kwds):
        unittest.TestCase.__init__(self, *args, **kwds)
        self.xml_re = re.compile('((timestamp)|(version))="[^"]*"')

    def compare_xml(self):
        F = open("coverage.xml")
        testData = self.xml_re.sub('\\1=""',F.read()).replace("\r","")
        F.close()
        F = open("reference/coverage.xml")
        refData = self.xml_re.sub('\\1=""',F.read()).replace("\r","")
        F.close()
        self.assertSequenceEqual(testData.split('\n'), refData.split('\n'))

GcovrXml = unittest.category('smoke')(GcovrXml)


def run(cmd):
    try:
        proc = subprocess.Popen( cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT )
        sys.stdout.write("%s"%proc.communicate()[0])
        return not proc.returncode
    except Exception:
        e = sys.exc_info()[1]
        sys.stdout.write("Caught unexpected exception in test driver: %s\n%s"
                         % ( str(e), traceback.format_exc() ))
        raise
    

    

@unittest.nottest
def gcovr_test_txt(self, name):
    os.chdir(os.path.join(basedir,name))
    run(["make"]) or self.fail("Make failed")
    run(["make","txt"]) or self.fail("Execution failed")
    self.assertFileEqualsBaseline("coverage.txt", "reference/coverage.txt")
    run(["make","clean"]) or self.fail("Clean failed")
    os.chdir(basedir)

@unittest.nottest
def gcovr_test_xml(self, name):
    os.chdir(os.path.join(basedir,name))
    run(["make"]) or self.fail("Make failed")
    run(["make","xml"]) or self.fail("Execution failed")
    self.compare_xml()
    run(["make","clean"]) or self.fail("Clean failed")
    os.chdir(basedir)

skip_dirs = [ '.', '..', '.svn' ]

for f in os.listdir(basedir):
    if os.path.isdir(os.path.join(basedir,f)) and f not in skip_dirs:
        GcovrTxt.add_fn_test(fn=gcovr_test_txt, name=f)
        GcovrXml.add_fn_test(fn=gcovr_test_xml, name=f)
	
if __name__ == "__main__":
    unittest.main()
