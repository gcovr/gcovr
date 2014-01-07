#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
#  _________________________________________________________________________

from .version import version_str

try:
    import html
except:
    import cgi as html

import os
import sys
import time
import shutil
import datetime
import posixpath

medium_coverage = 75.0
high_coverage = 90.0
low_color = "danger"
medium_color = "warning"
high_color = "success"
covered_color = "covered"
uncovered_color = "uncovered"

from jinja2 import Environment, PackageLoader, Template


env = Environment(loader=PackageLoader('gcovr'))

#
# A string template for the root HTML output
#
root_page = env.get_template('index.html')

#
# A string template for the source file HTML output
#
source_page = env.get_template('source.html')


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == os.errno.EEXIST and os.path.isdir(path):
            pass


def copy_static_content(options):
    from pkg_resources import resource_filename

    css_path = os.path.join(os.path.dirname(options.output), 'css')

    resource = resource_filename(__name__, 'static/css')
    makedirs(css_path)
    for file in os.listdir(resource):
        shutil.copy(os.path.join(resource, file), css_path)


def coverage_info(covdata, show_branch):
    total = 0
    covered = 0
    for key in covdata.keys():
        (t, c, p) = covdata[key].coverage(show_branch)
        total += t
        covered += c

    coverage = 0.0 if total == 0 else round(100.0 * covered / total, 1)
    if coverage < medium_coverage:
        return (total, covered, coverage, low_color)
    elif coverage < high_coverage:
        return (total, covered, coverage, medium_color)
    else:
        return (total, covered, coverage, high_color)


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
            return -1.0*covered/total
        else:
            return total or 1e6

    def _alpha(key):
        return key

    if options.output is None:
        options.output = u"index.html"
        options.html_details = False
    if options.output and options.output[-1] == os.sep:
        makedirs(options.output)
        options.output = os.path.join(options.output, u"index.html")

    copy_static_content(options)

    data = {}
    data['HEAD'] = "Head"
    data['VERSION'] = version_str()
    data['TIME'] = str(int(time.time()))
    data['DATE'] = datetime.date.today().isoformat()
    data['ROWS'] = []
    data['low_color'] = low_color
    data['medium_color'] = medium_color
    data['high_color'] = high_color
    data['COVERAGE_MED'] = medium_coverage
    data['COVERAGE_HIGH'] = high_coverage
    data['DIRECTORY'] = ''

    (total, covered, coverage, color) = coverage_info(covdata, True)

    data['BRANCHES_EXEC'] = str(covered)
    data['BRANCHES_TOTAL'] = str(total)
    data['BRANCHES_COVERAGE'] = str(coverage)
    data['BRANCHES_COLOR'] = color

    (total, covered, coverage, color) = coverage_info(covdata, False)

    data['LINES_EXEC'] = str(covered)
    data['LINES_TOTAL'] = str(total)
    data['LINES_COVERAGE'] = str(coverage)
    data['LINES_COLOR'] = color

    # Generate the coverage output (on a per-package basis)
    files = []
    keys = list(covdata.keys())
    sort_uncovered = options.sort_uncovered and _num_uncovered
    sort_percent = options.sort_percent and _percent_uncovered
    keys.sort(key=sort_uncovered or sort_percent or _alpha)

    filtered_fname = None

    for f in keys:
        cdata = covdata[f]
        filtered_fname = options.root_filter.sub('', f)
        print filtered_fname
        files.append(filtered_fname)
        cdata._filename = filtered_fname
        ttmp = os.path.abspath(options.output).split('.')
        if len(ttmp) > 1:
            cdata._sourcefile = ('.'.join(ttmp[:-1]) + '.' +
                                 cdata._filename.replace('/', '_') + '.' +
                                 ttmp[-1])
        else:
            cdata._sourcefile = (ttmp[0] + '.' +
                                 cdata._filename.replace('/', '_') + '.html')
    # Define the common root directory, which may differ from options.root
    # when source files share a common prefix.
    if len(files) > 1:
        commondir = posixpath.commonprefix(files)
        if commondir != '':
            data['DIRECTORY'] = commondir
    else:
        print filtered_fname
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
                coverage = 100*b_hits/len(branches)
                class_branch_hits += b_hits
                class_branches += len(branches)

        if class_lines == 0:
            lines_covered = 100.0
        else:
            lines_covered = 100.0 * class_hits / class_lines
        if class_branches == 0:
            branches_covered = 100.0
        else:
            branches_covered = 100.0 * class_branch_hits / class_branches

        data['ROWS'].append(html_row(options.html_details, cdata._sourcefile,
                                     directory=data['DIRECTORY'],
                                     filename=cdata._filename,
                                     LinesExec=class_hits,
                                     LinesTotal=class_lines,
                                     LinesCoverage=lines_covered,
                                     BranchesExec=class_branch_hits,
                                     BranchesTotal=class_branches,
                                     BranchesCoverage=branches_covered))
    data['ROWS'] = '\n'.join(data['ROWS'])

    if data['DIRECTORY'] == '':
        data['DIRECTORY'] = "."

    htmlString = root_page.render(**data)

    if options.output is None:
        sys.stdout.write(htmlString+'\n')
    else:
        OUTPUT = open(options.output, 'w')
        OUTPUT.write(htmlString + '\n')
        OUTPUT.close()

    if options.html_details:
        print_html_details(keys, covdata, options)

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer
from pygments.lexers import get_lexer_for_filename


class GcovrHtmlFormatter(HtmlFormatter):
    def __init__(self, covdata, **options):
        HtmlFormatter.__init__(self, **options)
        self.covdata = covdata

    def wrap(self, source, outfile):
        linenum = 1
        cdata = self.covdata
        yield 0, u'''
<table class="table table-compact table-striped">
'''
        yield 0, u'''
<thead><tr><th>Line</th><th>Exec</th><th>Code</th></tr></thead><tbody>
'''
        for code, line in source:
            if code == 1:
                html_class = ""
                covered = ""
                if linenum in cdata.covered:
                    html_class = " success"
                    covered = str(cdata.covered.get(linenum, 0))
                elif linenum in cdata.uncovered:
                    html_class = " warning"

                l = u'<tr>'
                l += u'''
<td class="exec"><a name="l' + str(linenum) + '" href="#l
'''
                l += str(linenum) + '">' + str(linenum) + '</a></td>'
                l += u'<td class="exec">' + covered
                l += u'</td><td class="pre' + html_class + '">'
                l += line
                l += u'</td></tr>'
                linenum += 1
                yield 1, l
        yield 0, u'</tbody></table>'


def print_html_details(keys, covdata, options):
    #
    # Generate an HTML file for every source file
    #
    for f in keys:
        cdata = covdata[f]
        data = {}
        data['FILENAME'] = cdata._filename
        data['ROWS'] = ''

        options.show_branch = True
        branchTotal, branchCovered, tmp = cdata.coverage(options.show_branch)
        data['BRANCHES_EXEC'] = str(branchCovered)
        data['BRANCHES_TOTAL'] = str(branchTotal)
        if branchTotal == 0:
            coverage = 0.0
        else:
            coverage = round(100.0 * branchCovered / branchTotal, 1)
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
        if lineTotal == 0:
            coverage = 0.0
        else:
            coverage = round(100.0 * lineCovered / lineTotal, 1)
        data['LINES_COVERAGE'] = str(coverage)
        if coverage < medium_coverage:
            data['LINES_COLOR'] = low_color
        elif coverage < high_coverage:
            data['LINES_COLOR'] = medium_color
        else:
            data['LINES_COLOR'] = high_color

        currdir = os.getcwd()
        os.chdir(options.root_dir)

        INPUT = open(data['FILENAME'], 'rb')
        code = INPUT.read()
        formatter = GcovrHtmlFormatter(cdata)
        try:
            lexer = get_lexer_for_filename(data['FILENAME'], code,
                                           encoding="utf-8")
        except:
            lexer = TextLexer()
        buf = highlight(code, lexer, formatter)
        data['ROWS'] = buf.encode('utf-8').decode('utf-8')

        os.chdir(currdir)
        try:
            htmlString = source_page.render(**data)

            with open(cdata._sourcefile, 'w') as f:
                f.write(htmlString.encode('utf-8'))
        except:
            print htmlString.__class__
            print buf
            raise


def source_row(lineno, source, cdata):
    rowstr = Template(u'''
    <tr>
    <td>{{lineno}}</td>
    <td class="{{covclass}}">{{linecount}}</td>
    <td class="{{covclass}}">{{source}}</td>
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
    return rowstr.render(**kwargs)


nrows = 0


#
# Generate the table row for a single file
#
def html_row(details, sourcefile, **kwargs):
    rowstr = Template(u'''
    <tr>
      <td>{{filename}}</td>
      <td>
        <div class="progress">
            <div class="progress-bar progress-bar-{{LinesBar}}"
                 role="progressbar"
                 aria-valuenow="{{LinesCoverage}}"
                 aria-valuemin="0" aria-valuemax="100"
                 style="width: {{LinesCoverage}}%;"></div>
            <span class="sr-only">{{LinesCoverage}}&nbsp;%</span>
        </div>
      </td>
      <td class="{{LinesColor}}">{{LinesCoverage}}&nbsp;%</td>
      <td class="{{LinesColor}}">{{LinesExec}} / {{LinesTotal}}</td>
      <td class="{{BranchesColor}}">{{BranchesCoverage}}&nbsp;%</td>
      <td class="{{BranchesColor}}">{{BranchesExec}} / {{BranchesTotal}}</td>
    </tr>
''')
    global nrows
    nrows += 1
    if details:
        sourcedir = kwargs['filename'][len(kwargs['directory']):]
        kwargs['filename'] = '<a href="%s">%s</a>' % (sourcefile, sourcedir)
    else:
        kwargs['filename'] = kwargs['filename'][len(kwargs['directory']):]
    kwargs['LinesCoverage'] = round(kwargs['LinesCoverage'], 1)
    if kwargs['LinesCoverage'] < medium_coverage:
        kwargs['LinesColor'] = 'danger'
        kwargs['LinesBar'] = 'danger'
    elif kwargs['LinesCoverage'] < high_coverage:
        kwargs['LinesColor'] = 'warning'
        kwargs['LinesBar'] = 'warning'
    else:
        kwargs['LinesColor'] = 'success'
        kwargs['LinesBar'] = 'success'

    kwargs['BranchesCoverage'] = round(kwargs['BranchesCoverage'], 1)
    if kwargs['BranchesCoverage'] < medium_coverage:
        kwargs['BranchesColor'] = 'danger'
        kwargs['BranchesBar'] = 'danger'
    elif kwargs['BranchesCoverage'] < high_coverage:
        kwargs['BranchesColor'] = 'warning'
        kwargs['BranchesBar'] = 'warning'
    else:
        kwargs['BranchesColor'] = 'success'
        kwargs['BranchesBar'] = 'success'

    return rowstr.render(**kwargs)
