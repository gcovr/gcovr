# -*- coding:utf-8 -*-
#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________

from __future__ import absolute_import

try:
    import html
except:
    import cgi as html

import os
import sys
import re

from time import time
from string import Template
from datetime import date
from posixpath import commonprefix

from ..version import version_str


medium_coverage = 75.0
high_coverage = 90.0
low_color = "LightPink"
medium_color = "#FFFF55"
high_color = "LightGreen"
covered_color = "LightGreen"
uncovered_color = "LightPink"

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

    .linecount
    {
        border-right: 1px gray solid;
        background-color: lightgray;
    }

    .src
    {
        padding-left: 12px;
    }

    .srcHeader
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
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
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
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
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
      <td width="10%" align="right" class="srcHeader">Exec</td>
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


#
# Produce an HTML report
#
def print_html_report(covdata, options):
    def _num_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        return total - covered

    def _percent_uncovered(key):
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
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
    data['TIME'] = str(int(time()))
    data['DATE'] = date.today().isoformat()
    data['ROWS'] = []
    data['low_color'] = low_color
    data['medium_color'] = medium_color
    data['high_color'] = high_color
    data['COVERAGE_MED'] = medium_coverage
    data['COVERAGE_HIGH'] = high_coverage
    data['CSS'] = css.substitute(
        low_color=low_color, medium_color=medium_color, high_color=high_color,
        covered_color=covered_color, uncovered_color=uncovered_color
    )
    data['DIRECTORY'] = ''

    branchTotal = 0
    branchCovered = 0
    options.show_branch = True
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        branchTotal += total
        branchCovered += covered
    data['BRANCHES_EXEC'] = str(branchCovered)
    data['BRANCHES_TOTAL'] = str(branchTotal)
    coverage = 0.0 if branchTotal == 0 else \
        round(100.0 * branchCovered / branchTotal, 1)
    data['BRANCHES_COVERAGE'] = str(coverage)
    if coverage < medium_coverage:
        data['BRANCHES_COLOR'] = low_color
    elif coverage < high_coverage:
        data['BRANCHES_COLOR'] = medium_color
    else:
        data['BRANCHES_COLOR'] = high_color

    lineTotal = 0
    lineCovered = 0
    options.show_branch = False
    for key in covdata.keys():
        (total, covered, percent) = covdata[key].coverage(options.show_branch)
        lineTotal += total
        lineCovered += covered
    data['LINES_EXEC'] = str(lineCovered)
    data['LINES_TOTAL'] = str(lineTotal)
    coverage = 0.0 if lineTotal == 0 else \
        round(100.0 * lineCovered / lineTotal, 1)
    data['LINES_COVERAGE'] = str(coverage)
    if coverage < medium_coverage:
        data['LINES_COLOR'] = low_color
    elif coverage < high_coverage:
        data['LINES_COLOR'] = medium_color
    else:
        data['LINES_COLOR'] = high_color

    # Generate the coverage output (on a per-package basis)
    #source_dirs = set()
    files = []
    filtered_fname = ''
    keys = list(covdata.keys())
    keys.sort(
        key=options.sort_uncovered and _num_uncovered or
        options.sort_percent and _percent_uncovered or _alpha
    )

    # These path separators are not allowed in the file name part
    PATH_CHAR_RE = re.compile(r'[/\\:]')

    for f in keys:
        cdata = covdata[f]
        filtered_fname = options.root_filter.sub('', f)
        files.append(filtered_fname)
        cdata._filename = filtered_fname
        path, ext = os.path.splitext(os.path.abspath(options.output))
        if not ext:
            ext = '.html'
        cdata._sourcefile = '%s.%s%s' % (
            path, PATH_CHAR_RE.sub('_', cdata._filename), ext)
    # Define the common root directory, which may differ from options.root
    # when source files share a common prefix.
    if len(files) > 1:
        commondir = commonprefix(files)
        if commondir != '':
            data['DIRECTORY'] = commondir
    else:
        dir_, file_ = os.path.split(filtered_fname)
        if dir_ != '':
            data['DIRECTORY'] = dir_ + os.sep

    for f in keys:
        cdata = covdata[f]
        class_lines = 0
        class_hits = 0
        class_branches = 0
        class_branch_hits = 0
        for line in cdata.all_lines:
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

        lines_covered = 100.0 if class_lines == 0 else \
            100.0 * class_hits / class_lines
        branches_covered = 100.0 if class_branches == 0 else \
            100.0 * class_branch_hits / class_branches

        data['ROWS'].append(html_row(
            options, cdata._sourcefile,
            directory=data['DIRECTORY'],
            filename=cdata._filename,
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

        options.show_branch = True
        branchTotal, branchCovered, tmp = cdata.coverage(options.show_branch)
        data['BRANCHES_EXEC'] = str(branchCovered)
        data['BRANCHES_TOTAL'] = str(branchTotal)
        coverage = 0.0 if branchTotal == 0 else \
            round(100.0 * branchCovered / branchTotal, 1)
        data['BRANCHES_COVERAGE'] = str(coverage)
        if coverage < medium_coverage:
            data['BRANCHES_COLOR'] = low_color
        elif coverage < high_coverage:
            data['BRANCHES_COLOR'] = medium_color
        else:
            data['BRANCHES_COLOR'] = high_color

        options.show_branch = False
        lineTotal, lineCovered, tmp = cdata.coverage(options.show_branch)
        data['LINES_EXEC'] = str(lineCovered)
        data['LINES_TOTAL'] = str(lineTotal)
        coverage = 0.0 if lineTotal == 0 else \
            round(100.0 * lineCovered / lineTotal, 1)
        data['LINES_COVERAGE'] = str(coverage)
        if coverage < medium_coverage:
            data['LINES_COLOR'] = low_color
        elif coverage < high_coverage:
            data['LINES_COLOR'] = medium_color
        else:
            data['LINES_COLOR'] = high_color

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
    <td align="right" class="linecount ${covclass}"><pre>${linecount}</pre></td>
    <td align="left" class="src ${covclass}"><pre>${source}</pre></td>
    </tr>''')
    kwargs = {}
    kwargs['lineno'] = str(lineno)
    if lineno in cdata.covered:
        kwargs['covclass'] = 'coveredLine'
        kwargs['linecount'] = str(cdata.covered.get(lineno, 0))
    elif lineno in cdata.uncovered:
        kwargs['covclass'] = 'uncoveredLine'
        kwargs['linecount'] = ''
    else:
        kwargs['covclass'] = ''
        kwargs['linecount'] = ''
    kwargs['source'] = html.escape(source)
    return rowstr.substitute(**kwargs)

#
# Generate the table row for a single file
#
nrows = 0


def html_row(options, sourcefile, **kwargs):
    details = options.html_details
    if options.relative_anchors:
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
    global nrows
    nrows += 1
    if nrows % 2 == 0:
        kwargs['altstyle'] = 'style="background-color:LightSteelBlue"'
    else:
        kwargs['altstyle'] = ''
    if details:
        kwargs['filename'] = '<a href="%s">%s</a>' % (
            sourcefile, kwargs['filename'][len(kwargs['directory']):]
        )
    else:
        kwargs['filename'] = kwargs['filename'][len(kwargs['directory']):]
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

    kwargs['BranchesCoverage'] = round(kwargs['BranchesCoverage'], 1)
    if kwargs['BranchesCoverage'] < medium_coverage:
        kwargs['BranchesColor'] = low_color
        kwargs['BranchesBar'] = 'red'
    elif kwargs['BranchesCoverage'] < high_coverage:
        kwargs['BranchesColor'] = medium_color
        kwargs['BranchesBar'] = 'yellow'
    else:
        kwargs['BranchesColor'] = high_color
        kwargs['BranchesBar'] = 'green'

    return rowstr.substitute(**kwargs)
