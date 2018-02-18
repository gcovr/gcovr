# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.

try:
    import html
except ImportError:
    import cgi as html

import os
import sys
import time
import datetime
import zlib

from string import Template

from .version import version_str
from .utils import commonpath

medium_coverage = 75.0
high_coverage = 90.0
low_color = "LightPink"
medium_color = "#FFFF55"
high_color = "LightGreen"
covered_color = "LightGreen"
uncovered_color = "LightPink"
takenBranch_color = "Green"
notTakenBranch_color = "Red"


#
# CSS declarations for the HTML output
#
css = Template('''
    body
    {
      color: #000000;
      background-color: #FFFFFF;
    }

    /* Link formats: use maroon w/underlines */
    a:link
    {
      color: navy;
      text-decoration: underline;
    }
    a:visited
    {
      color: maroon;
      text-decoration: underline;
    }
    a:active
    {
      color: navy;
      text-decoration: underline;
    }

    /*** TD formats ***/
    td
    {
      font-family: sans-serif;
    }
    td.title
    {
      text-align: center;
      padding-bottom: 10px;
      font-size: 20pt;
      font-weight: bold;
    }

    /* TD Header Information */
    td.headerName
    {
      text-align: right;
      color: black;
      padding-right: 6px;
      font-weight: bold;
      vertical-align: top;
      white-space: nowrap;
    }
    td.headerValue
    {
      text-align: left;
      color: blue;
      font-weight: bold;
      white-space: nowrap;
    }
    td.headerTableEntry
    {
      text-align: right;
      color: black;
      font-weight: bold;
      white-space: nowrap;
      padding-left: 12px;
      padding-right: 4px;
      background-color: LightBlue;
    }
    td.headerValueLeg
    {
      text-align: left;
      color: black;
      font-size: 80%;
      white-space: nowrap;
      padding-left: 10px;
      padding-right: 10px;
      padding-top: 2px;
    }

    /* Color of horizontal ruler */
    td.hr
    {
      background-color: navy;
      height:3px;
    }
    /* Footer format */
    td.footer
    {
      text-align: center;
      padding-top: 3px;
      font-family: sans-serif;
    }

    /* Coverage Table */

    td.coverTableHead
    {
      text-align: center;
      color: white;
      background-color: SteelBlue;
      font-family: sans-serif;
      font-size: 120%;
      white-space: nowrap;
      padding-left: 4px;
      padding-right: 4px;
    }
    td.coverFile
    {
      text-align: left;
      padding-left: 10px;
      padding-right: 20px;
      color: black;
      background-color: LightBlue;
      font-family: monospace;
      font-weight: bold;
      font-size: 110%;
    }
    td.coverBar
    {
      padding-left: 10px;
      padding-right: 10px;
      background-color: LightBlue;
    }
    td.coverBarOutline
    {
      background-color: white;
    }
    td.coverValue
    {
      padding-top: 2px;
      text-align: right;
      padding-left: 10px;
      padding-right: 10px;
      font-family: sans-serif;
      white-space: nowrap;
      font-weight: bold;
    }

    /* Link Details */
    a.detail:link
    {
      color: #B8D0FF;
      font-size:80%;
    }
    a.detail:visited
    {
      color: #B8D0FF;
      font-size:80%;
    }
    a.detail:active
    {
      color: #FFFFFF;
      font-size:80%;
    }

    .graphcont{
        color:#000;
        font-weight:700;
        float:left
    }

    .graph{
        float:left;
        background-color: white;
        position:relative;
        width:280px;
        padding:0
    }

    .graph .bar{
        display:block;
        position:relative;
        border:black 1px solid;
        text-align:center;
        color:#fff;
        height:10px;
        font-family:Arial,Helvetica,sans-serif;
        font-size:12px;
        line-height:1.9em
    }

    .graph .bar span{
        position:absolute;
        left:1em
    }

    td.coveredLine,
    span.coveredLine
    {
        background-color: ${covered_color}!important;
    }

    td.uncoveredLine,
    span.uncoveredLine
    {
        background-color: ${uncovered_color}!important;
    }

    .linebranch, .linecount
    {
        border-right: 1px gray solid;
        background-color: lightgray;
    }

    span.takenBranch
    {
        color: ${takenBranch_color}!important;
        cursor: help;
    }

    span.notTakenBranch
    {
        color: ${notTakenBranch_color}!important;
        cursor: help;
    }

    .src
    {
        padding-left: 12px;
    }

    .srcHeader,
    span.takenBranch,
    span.notTakenBranch
    {
        font-family: monospace;
        font-weight: bold;
    }

    pre
    {
        height : 15px;
        margin-top: 0;
        margin-bottom: 0;
    }

    .lineno
    {
        background-color: #EFE383;
        border-right: 1px solid #BBB15F;
    }
''')

#
# A string template for the root HTML output
#
root_page = Template('''
<html>

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=${ENC}"/>
  <title>${HEAD}</title>
  <style media="screen" type="text/css">
  ${CSS}
  </style>
</head>

<body>

  <table width="100%" border=0 cellspacing=0 cellpadding=0>
    <tr><td class="title">GCC Code Coverage Report</td></tr>
    <tr><td class="hr"></td></tr>

    <tr>
      <td width="100%">
        <table cellpadding=1 border=0 width="100%">
          <tr>
            <td width="10%" class="headerName">Directory:</td>
            <td width="35%" class="headerValue">${DIRECTORY}</td>
            <td width="5%"></td>
            <td width="15%"></td>
            <td width="10%" class="headerValue" style="text-align:right;">Exec</td>
            <td width="10%" class="headerValue" style="text-align:right;">Total</td>
            <td width="15%" class="headerValue" style="text-align:right;">Coverage</td>
          </tr>
          <tr>
            <td class="headerName">Date:</td>
            <td class="headerValue">${DATE}</td>
            <td></td>
            <td class="headerName">Lines:</td>
            <td class="headerTableEntry">${LINES_EXEC}</td>
            <td class="headerTableEntry">${LINES_TOTAL}</td>
            <td class="headerTableEntry" style="background-color:${LINES_COLOR}">${LINES_COVERAGE} %</td>
          </tr>
          <tr>
            <td class="headerName">Legend:</td>
            <td class="headerValueLeg">
              <span style="background-color:${low_color}">low: &lt; ${COVERAGE_MED} %</span>
              <span style="background-color:${medium_color}">medium: &gt;= ${COVERAGE_MED} %</span>
              <span style="background-color:${high_color}">high: &gt;= ${COVERAGE_HIGH} %</span>
            </td>
            <td></td>
            <td class="headerName">Branches:</td>
            <td class="headerTableEntry">${BRANCHES_EXEC}</td>
            <td class="headerTableEntry">${BRANCHES_TOTAL}</td>
            <td class="headerTableEntry" style="background-color:${BRANCHES_COLOR}">${BRANCHES_COVERAGE} %</td>
          </tr>
        </table>
      </td>
    </tr>

    <tr><td class="hr"></td></tr>
  </table>

  <center>
  <table width="80%" cellpadding=1 cellspacing=1 border=0>
    <tr>
      <td width="44%"><br></td>
      <td width="8%"></td>
      <td width="8%"></td>
      <td width="8%"></td>
      <td width="8%"></td>
      <td width="8%"></td>
    </tr>
    <tr>
      <td class="coverTableHead">File</td>
      <td class="coverTableHead" colspan=3>Lines</td>
      <td class="coverTableHead" colspan=2>Branches</td>
    </tr>

    ${ROWS}

    <tr>
      <td width="44%"><br></td>
      <td width="8%"></td>
      <td width="8%"></td>
      <td width="8%"></td>
      <td width="8%"></td>
      <td width="8%"></td>
    </tr>
  </table>
  </center>

  <table width="100%" border=0 cellspacing=0 cellpadding=0>
    <tr><td class="hr"><td></tr>
    <tr><td class="footer">Generated by: <a href="http://gcovr.com">GCOVR (Version ${VERSION})</a></td></tr>
  </table>
  <br>

</body>

</html>
''')

#
# A string template for the source file HTML output
#
source_page = Template('''
<html>

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=${ENC}"/>
  <title>${HEAD}</title>
  <style media="screen" type="text/css">
  ${CSS}
  </style>
</head>

<body>

  <table width="100%" border="0" cellspacing="0" cellpadding="0">
    <tr><td class="title">GCC Code Coverage Report</td></tr>
    <tr><td class="hr"></td></tr>

    <tr>
      <td width="100%">
        <table cellpadding="1" border="0" width="100%">
          <tr>
            <td width="10%" class="headerName">Directory:</td>
            <td width="35%" class="headerValue">${DIRECTORY}</td>
            <td width="5%"></td>
            <td width="15%"></td>
            <td width="10%" class="headerValue" style="text-align:right;">Exec</td>
            <td width="10%" class="headerValue" style="text-align:right;">Total</td>
            <td width="15%" class="headerValue" style="text-align:right;">Coverage</td>
          </tr>
          <tr>
            <td class="headerName">File:</td>
            <td class="headerValue">${FILENAME}</td>
            <td></td>
            <td class="headerName">Lines:</td>
            <td class="headerTableEntry">${LINES_EXEC}</td>
            <td class="headerTableEntry">${LINES_TOTAL}</td>
            <td class="headerTableEntry" style="background-color:${LINES_COLOR}">${LINES_COVERAGE} %</td>
          </tr>
          <tr>
            <td class="headerName">Date:</td>
            <td class="headerValue">${DATE}</td>
            <td></td>
            <td class="headerName">Branches:</td>
            <td class="headerTableEntry">${BRANCHES_EXEC}</td>
            <td class="headerTableEntry">${BRANCHES_TOTAL}</td>
            <td class="headerTableEntry" style="background-color:${BRANCHES_COLOR}">${BRANCHES_COVERAGE} %</td>
          </tr>
        </table>
      </td>
    </tr>

    <tr><td class="hr"></td></tr>
  </table>

  <br>
  <table cellspacing="0" cellpadding="1">
    <tr>
      <td width="5%" align="right" class="srcHeader">Line</td>
      <td width="5%" align="right" class="srcHeader">Branch</td>
      <td width="5%" align="right" class="srcHeader">Exec</td>
      <td width="75%" align="left" class="srcHeader src">Source</td>
    </tr>

    ${ROWS}

  </table>
  <br>

  <table width="100%" border="0" cellspacing="0" cellpadding="0">
    <tr><td class="hr"><td></tr>
    <tr><td class="footer">Generated by: <a href="http://gcovr.com">GCOVR (Version ${VERSION})</a></td></tr>
  </table>
  <br>

</body>

</html>
''')


def calculate_coverage(covered, total, nan_value=0.0):
    return nan_value if total == 0 else round(100.0 * covered / total, 1)


def coverage_to_color(coverage):
    if coverage is None:
        return 'LightGray'
    elif coverage < medium_coverage:
        return low_color
    elif coverage < high_coverage:
        return medium_color
    else:
        return high_color


#
# Produce an HTML report
#
def print_html_report(covdata, options):
    def _num_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(show_branch=False)
        return total - covered

    def _percent_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(show_branch=False)
        if covered:
            return -1.0 * covered / total
        else:
            return total or 1e6

    def _alpha(key):
        return key

    details = options.html_details
    if options.output is None:
        details = False
    data = {}
    data['HEAD'] = "Head"
    data['VERSION'] = version_str()
    data['TIME'] = str(int(time.time()))
    data['DATE'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data['ROWS'] = []
    data['ENC'] = options.html_encoding
    data['low_color'] = low_color
    data['medium_color'] = medium_color
    data['high_color'] = high_color
    data['COVERAGE_MED'] = medium_coverage
    data['COVERAGE_HIGH'] = high_coverage
    data['CSS'] = css.substitute(
        low_color=low_color,
        medium_color=medium_color,
        high_color=high_color,
        covered_color=covered_color,
        uncovered_color=uncovered_color,
        takenBranch_color=takenBranch_color,
        notTakenBranch_color=notTakenBranch_color
    )
    data['DIRECTORY'] = ''

    branchTotal = 0
    branchCovered = 0
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=True)
        branchTotal += total
        branchCovered += covered
    data['BRANCHES_EXEC'] = str(branchCovered)
    data['BRANCHES_TOTAL'] = str(branchTotal)
    coverage = calculate_coverage(branchCovered, branchTotal, nan_value=None)
    data['BRANCHES_COVERAGE'] = '-' if coverage is None else str(coverage)
    data['BRANCHES_COLOR'] = coverage_to_color(coverage)

    lineTotal = 0
    lineCovered = 0
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(show_branch=False)
        lineTotal += total
        lineCovered += covered
    data['LINES_EXEC'] = str(lineCovered)
    data['LINES_TOTAL'] = str(lineTotal)
    coverage = calculate_coverage(lineCovered, lineTotal)
    data['LINES_COVERAGE'] = str(coverage)
    data['LINES_COLOR'] = coverage_to_color(coverage)

    # Generate the coverage output (on a per-package basis)
    # source_dirs = set()
    files = []
    dirs = []
    filtered_fname = ''
    keys = list(covdata.keys())
    keys.sort(
        key=options.sort_uncovered and _num_uncovered or
        options.sort_percent and _percent_uncovered or _alpha
    )
    for f in keys:
        cdata = covdata[f]
        filtered_fname = options.root_filter.sub('', f)
        files.append(filtered_fname)
        dirs.append(os.path.dirname(filtered_fname) + os.sep)
        cdata._filename = filtered_fname
        if not details:
            cdata._sourcefile = None
        else:
            ttmp = os.path.abspath(options.output).split('.')
            longname = cdata._filename.replace(os.sep, '_')
            longname_hash = ""
            while True:
                if len(ttmp) > 1:
                    cdata._sourcefile = \
                        '.'.join(ttmp[:-1]) + \
                        '.' + longname + longname_hash + \
                        '.' + ttmp[-1]
                else:
                    cdata._sourcefile = \
                        ttmp[0] + '.' + longname + longname_hash + '.html'
                # we add a hash at the end and attempt to shorten the
                # filename if it exceeds common filesystem limitations
                if len(os.path.basename(cdata._sourcefile)) < 256:
                    break
                longname_hash = "_" + hex(zlib.crc32(longname) & 0xffffffff)[2:]
                longname = longname[(len(cdata._sourcefile) - len(longname_hash)):]

    # Define the common root directory, which may differ from options.root
    # when source files share a common prefix.
    if len(files) > 1:
        commondir = commonpath(files)
        if commondir != '':
            data['DIRECTORY'] = commondir
    else:
        dir_, file_ = os.path.split(filtered_fname)
        if dir_ != '':
            data['DIRECTORY'] = dir_ + os.sep

    nrows = 0
    for f in keys:
        cdata = covdata[f]
        class_lines = 0
        class_hits = 0
        class_branches = 0
        class_branch_hits = 0
        for line in sorted(cdata.all_lines):
            hits = cdata.covered.get(line, 0)
            class_lines += 1
            if hits > 0:
                class_hits += 1
            branches = cdata.branches.get(line)
            if branches is None:
                pass
            else:
                b_hits = 0
                for v in branches.values():
                    if v > 0:
                        b_hits += 1
                coverage = 100 * b_hits / len(branches)
                class_branch_hits += b_hits
                class_branches += len(branches)

        lines_covered = calculate_coverage(class_hits, class_lines, nan_value=100.0)
        branches_covered = calculate_coverage(class_branch_hits, class_branches, nan_value=None)

        nrows += 1
        data['ROWS'].append(html_row(
            options, details, cdata._sourcefile, nrows,
            directory=data['DIRECTORY'],
            filename=os.path.relpath(
                os.path.realpath(cdata._filename), data['DIRECTORY']),
            LinesExec=class_hits,
            LinesTotal=class_lines,
            LinesCoverage=lines_covered,
            BranchesExec=class_branch_hits,
            BranchesTotal=class_branches,
            BranchesCoverage=branches_covered
        ))
    data['ROWS'] = '\n'.join(data['ROWS'])

    if data['DIRECTORY'] == '':
        data['DIRECTORY'] = "."
    data['DIRECTORY'] = data['DIRECTORY'].replace('\\', '/')

    htmlString = root_page.substitute(**data)

    if options.output is None:
        sys.stdout.write(htmlString + '\n')
    else:
        OUTPUT = open(options.output, 'w')
        OUTPUT.write(htmlString + '\n')
        OUTPUT.close()

    # Return, if no details are requested
    if not details:
        return

    #
    # Generate an HTML file for every source file
    #
    for f in keys:
        cdata = covdata[f]

        data['FILENAME'] = cdata._filename
        data['ROWS'] = ''

        branchTotal, branchCovered, tmp = cdata.coverage(show_branch=True)
        data['BRANCHES_EXEC'] = str(branchCovered)
        data['BRANCHES_TOTAL'] = str(branchTotal)
        coverage = calculate_coverage(branchCovered, branchTotal, nan_value=None)
        data['BRANCHES_COVERAGE'] = '-' if coverage is None else str(coverage)
        data['BRANCHES_COLOR'] = coverage_to_color(coverage)

        lineTotal, lineCovered, tmp = cdata.coverage(show_branch=False)
        data['LINES_EXEC'] = str(lineCovered)
        data['LINES_TOTAL'] = str(lineTotal)
        coverage = calculate_coverage(lineCovered, lineTotal)
        data['LINES_COVERAGE'] = str(coverage)
        data['LINES_COLOR'] = coverage_to_color(coverage)

        data['ROWS'] = []
        currdir = os.getcwd()
        os.chdir(options.root_dir)
        INPUT = open(data['FILENAME'], 'r')
        ctr = 1
        for line in INPUT:
            data['ROWS'].append(
                source_row(ctr, line.rstrip(), cdata)
            )
            ctr += 1
        INPUT.close()
        os.chdir(currdir)
        data['ROWS'] = '\n'.join(data['ROWS'])

        htmlString = source_page.substitute(**data)
        OUTPUT = open(cdata._sourcefile, 'w')
        OUTPUT.write(htmlString + '\n')
        OUTPUT.close()


def source_row(lineno, source, cdata):
    rowstr = Template('''
    <tr>
    <td align="right" class="lineno"><pre>${lineno}</pre></td>
    <td align="right" class="linebranch">${linebranch}</td>
    <td align="right" class="linecount ${covclass}"><pre>${linecount}</pre></td>
    <td align="left" class="src ${covclass}"><pre>${source}</pre></td>
    </tr>''')
    kwargs = {}
    kwargs['lineno'] = str(lineno)
    if lineno in cdata.covered:
        kwargs['covclass'] = 'coveredLine'
        kwargs['linebranch'] = ''
        # If line has branches them show them with ticks or crosses
        if lineno in cdata.branches.keys():
            branches = cdata.branches.get(lineno)
            branchcounter = 0
            for branch in branches:
                if branches[branch] > 0:
                    kwargs['linebranch'] += '<span class="takenBranch" title="Branch ' + str(branch) + ' taken ' + str(branches[branch]) + ' times">&check;</span>'
                else:
                    kwargs['linebranch'] += '<span class="notTakenBranch" title="Branch ' + str(branch) + ' not taken">&cross;</span>'
                branchcounter += 1
                # Wrap at 4 branches to avoid too wide column
                if (branchcounter > 0) and ((branchcounter % 4) == 0):
                    kwargs['linebranch'] += '<br/>'
        kwargs['linecount'] = str(cdata.covered.get(lineno, 0))
    elif lineno in cdata.uncovered:
        kwargs['covclass'] = 'uncoveredLine'
        kwargs['linebranch'] = ''
        kwargs['linecount'] = ''
    else:
        kwargs['covclass'] = ''
        kwargs['linebranch'] = ''
        kwargs['linecount'] = ''
    kwargs['source'] = html.escape(source)
    return rowstr.substitute(**kwargs)


#
# Generate the table row for a single file
#
def html_row(options, details, sourcefile, nrows, **kwargs):
    if details and options.relative_anchors:
        sourcefile = os.path.basename(sourcefile)
    rowstr = Template('''
    <tr>
      <td class="coverFile" ${altstyle}>${filename}</td>
      <td class="coverBar" align="center" ${altstyle}>
        <table border=0 cellspacing=0 cellpadding=1><tr><td class="coverBarOutline">
                <div class="graph"><strong class="bar" style="width:${LinesCoverage}%; ${BarBorder}background-color:${LinesBar}"></strong></div>
                </td></tr></table>
      </td>
      <td class="CoverValue" style="font-weight:bold; background-color:${LinesColor};">${LinesCoverage}&nbsp;%</td>
      <td class="CoverValue" style="font-weight:bold; background-color:${LinesColor};">${LinesExec} / ${LinesTotal}</td>
      <td class="CoverValue" style="background-color:${BranchesColor};">${BranchesCoverage}&nbsp;%</td>
      <td class="CoverValue" style="background-color:${BranchesColor};">${BranchesExec} / ${BranchesTotal}</td>
    </tr>
''')
    if nrows % 2 == 0:
        kwargs['altstyle'] = 'style="background-color:LightSteelBlue"'
    else:
        kwargs['altstyle'] = ''
    if details:
        kwargs['filename'] = '<a href="%s">%s</a>' % (
            sourcefile, kwargs['filename'].replace('\\', '/')
        )
    kwargs['LinesCoverage'] = round(kwargs['LinesCoverage'], 1)
    # Disable the border if the bar is too short to see the color
    if kwargs['LinesCoverage'] < 1e-7:
        kwargs['BarBorder'] = "border:white; "
    else:
        kwargs['BarBorder'] = ""
    if kwargs['LinesCoverage'] < medium_coverage:
        kwargs['LinesColor'] = low_color
        kwargs['LinesBar'] = 'red'
    elif kwargs['LinesCoverage'] < high_coverage:
        kwargs['LinesColor'] = medium_color
        kwargs['LinesBar'] = 'yellow'
    else:
        kwargs['LinesColor'] = high_color
        kwargs['LinesBar'] = 'green'

    kwargs['BranchesColor'] = coverage_to_color(kwargs['BranchesCoverage'])
    kwargs['BranchesCoverage'] = '-' if kwargs['BranchesCoverage'] is None else round(kwargs['BranchesCoverage'], 1)

    return rowstr.substitute(**kwargs)
