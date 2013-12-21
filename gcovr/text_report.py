#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________


import sys


#
# Produce the classic gcovr text report
#
def print_text_report(covdata, options):
    def _num_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        return total - covered
    def _percent_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        if covered:
            return -1.0*covered/total
        else:
            return total or 1e6
    def _alpha(key):
        return key

    if options.output:
        OUTPUT = open(options.output,'w')
    else:
        OUTPUT = sys.stdout
    total_lines=0
    total_covered=0
    # Header
    OUTPUT.write("-"*78 + '\n')
    a = options.show_branch and "Branches" or "Lines"
    b = options.show_branch and "Taken" or "Exec"
    c = "Missing"
    OUTPUT.write("File".ljust(40) + a.rjust(8) + b.rjust(8)+ "  Cover   " + c + "\n")
    OUTPUT.write("-"*78 + '\n')

    # Data
    keys = list(covdata.keys())
    keys.sort(key=options.sort_uncovered and _num_uncovered or \
              options.sort_percent and _percent_uncovered or _alpha)
    for key in keys:
        (t, n, txt) = covdata[key].summary(options)
        total_lines += t
        total_covered += n
        OUTPUT.write(txt + '\n')

    # Footer & summary
    OUTPUT.write("-"*78 + '\n')
    percent = total_lines and str(int(100.0*total_covered/total_lines)) or "--"
    OUTPUT.write("TOTAL".ljust(40) + str(total_lines).rjust(8) + \
          str(total_covered).rjust(8) + str(percent).rjust(6)+"%" + '\n')
    OUTPUT.write("-"*78 + '\n')

    # Close logfile
    if options.output:
        OUTPUT.close()


