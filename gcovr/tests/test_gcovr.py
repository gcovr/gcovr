#!/usr/bin/env python
import os
import os.path
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
        F = open('coverage.xml', 'w')
        F.write(testData)
        F.close()
        F = open("reference/coverage.xml")
        refData = self.xml_re.sub('\\1=""',F.read()).replace("\r","")
        F.close()
        F = open('reference/coverage.xml', 'w')
        F.write(refData)
        F.close()
        #self.assertSequenceEqual(testData.split('\n'), refData.split('\n'))
        self.assertMatchesXmlBaseline('coverage.xml', os.path.join('reference','coverage.xml'), tolerance=1e-4)

GcovrXml = unittest.category('smoke')(GcovrXml)


class GcovrHtml(unittest.TestCase):
    def __init__(self, *args, **kwds):
        unittest.TestCase.__init__(self, *args, **kwds)
        self.xml_re = re.compile('((timestamp)|(version))="[^"]*"')

    def compare_html(self):
        F = open("coverage.html")
        testData = self.xml_re.sub('\\1=""',F.read()).replace("\r","")
        F.close()
        F = open('coverage.html', 'w')
        F.write(testData)
        F.close()
        F = open("reference/coverage.html")
        refData = self.xml_re.sub('\\1=""',F.read()).replace("\r","")
        F.close()
        F = open('reference/coverage.html', 'w')
        F.write(refData)
        F.close()
        #self.assertSequenceEqual(testData.split('\n'), refData.split('\n'))
        self.assertMatchesXmlBaseline('coverage.html', os.path.join('reference','coverage.html'), tolerance=1e-4)

GcovrHtml = unittest.category('smoke')(GcovrHtml)


def run(cmd):
    try:
        proc = subprocess.Popen( cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 env=os.environ )
        print("STDOUT - START")
        sys.stdout.write("%s"%proc.communicate()[0])
        print("STDOUT - END")
        return not proc.returncode
    except Exception:
        e = sys.exc_info()[1]
        sys.stdout.write("Caught unexpected exception in test driver: %s\n%s"
                         % ( str(e), traceback.format_exc() ))
        raise
    

    

@unittest.nottest
def gcovr_test_txt(self, name):
    os.chdir(os.path.join(basedir,name))
    run(["make","clean"]) or self.fail("Clean failed")
    run(["make"]) or self.fail("Make failed")
    run(["make","txt"]) or self.fail("Execution failed")
    self.assertFileEqualsBaseline("coverage.txt", "reference/coverage.txt")
    run(["make","clean"]) or self.fail("Clean failed")
    os.chdir(basedir)

@unittest.nottest
def gcovr_test_xml(self, name):
    os.chdir(os.path.join(basedir,name))
    run(["make","clean"]) or self.fail("Clean failed")
    run(["make"]) or self.fail("Make failed")
    run(["make","xml"]) or self.fail("Execution failed")
    self.compare_xml()
    run(["make","clean"]) or self.fail("Clean failed")
    os.chdir(basedir)

@unittest.nottest
def gcovr_test_html(self, name):
    os.chdir(os.path.join(basedir,name))
    run(["make"]) or self.fail("Make failed")
    run(["make","html"]) or self.fail("Execution failed")
    self.compare_html()
    run(["make","clean"]) or self.fail("Clean failed")
    os.chdir(basedir)

skip_dirs = [ '.', '..', '.svn' ]

for f in os.listdir(basedir):
    if os.path.isdir(os.path.join(basedir,f)) and f not in skip_dirs:
        if 'pycache' in f:
            continue
        GcovrTxt.add_fn_test(fn=gcovr_test_txt, name=f)
        GcovrXml.add_fn_test(fn=gcovr_test_xml, name=f)
        #GcovrHtml.add_fn_test(fn=gcovr_test_html, name=f)
	
if __name__ == "__main__":
    unittest.main()
