#!/usr/bin/python

# Copyright 2009-2010 bjweeks, MZMcBride, svick

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import datetime
import os
import re
import subprocess
import sys
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

try:
    report_file_no_extension = sys.argv[1].split('.')[0]
except IndexError:
    print 'No report file name provided; exiting.'
    sys.exit()

report_filename = report_file_no_extension + '.py'

try:
    with open(report_filename, 'r') as report_file:
        report_source = report_file.read()
except IOError:
    print 'No such file; exiting.'
    sys.exit()

report_name = re.search('report_title =.*\'(.*)\'$', report_source, re.MULTILINE).group(1)

configuration_title = config.get('dbreps', 'rootpage') + report_name + '/Configuration'

crontab = subprocess.Popen('crontab -l', stdout = subprocess.PIPE, shell = True).communicate()[0]
crontab_line = re.search('^.*' + report_file_no_extension + '.*$', crontab, re.MULTILINE).group(0)

template = u'''
== %s ==
<source lang="python" enclose="div">
%s
</source>

== crontab ==
<pre style="white-space:pre-wrap">
%s
</pre>
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

configuration = wikitools.Page(wiki, configuration_title)
configuration_text = template % (report_filename, report_source, crontab_line)
configuration_text = configuration_text.encode('utf-8')
configuration.edit(configuration_text, summary=config.get('dbreps', 'editsumm') if len(sys.argv) < 3 else sys.argv[2], bot=1)
