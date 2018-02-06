from __future__ import print_function
import re
import sys
import os.path
import os


include_pattern = re.compile(r'include::([a-zA-Z0-9_.\-/]+\/)\.([^_]+)\_[a-zA-Z0-9]*\.(py|sh|h|cpp)\[\]')
anchor_start_pattern = re.compile('([^@]+)@([a-zA-Z0-9]+):')
anchor_end_pattern = re.compile('([^@]+)@:([a-zA-Z0-9]+)')


def process(dir, root, suffix):
    anchors = {}
    anchors[''] = open('%s.%s_.%s' % (dir, root, suffix), 'w')
    with open('%s%s.%s' % (dir, root, suffix), 'r') as INPUT:
        for line in INPUT:
            m = anchor_start_pattern.match(line)
            if m:
                anchor = m.group(2)
                anchor_file = '%s.%s_%s.%s' % (dir, root, anchor, suffix)
                anchors[anchor] = open(anchor_file, 'w')
                continue
            m = anchor_end_pattern.match(line)
            if m:
                anchor = m.group(2)
                anchors[anchor].close()
                del anchors[anchor]
                continue
            for anchor in anchors:
                print(line, file=anchors[anchor])
    for anchor in anchors:
        if anchor != '':
            print("ERROR: anchor '%s' did not terminate" % anchor)
        anchors[anchor].close()


processed = set()
for file in sys.argv[1:]:
    print("Processing file '%s' ..." % file)
    with open(file, 'r') as INPUT:
        for line in INPUT:
            m = include_pattern.match(line)
            if not m:
                continue
            directory, root, suffix = m.groups()
            filename = directory + root + '.' + suffix
            basename = directory + root
            if not os.path.exists(filename):
                print(line)
                print("ERROR: file '%s' does not exist!" % filename)
                sys.exit(1)
            if basename in processed:
                continue
            process(directory, root, suffix)
            processed.add(basename)
