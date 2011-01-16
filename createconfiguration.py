#!/usr/bin/env python2.5
 
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
 
import sys
import re
import subprocess
import datetime
import wikitools
import settings
 
report_filename = sys.argv[1]

report_file = open(report_filename, 'r')
report_source = report_file.read()

report_name = re.search('\'(.*)\'', report_source).group(1)

configuration_title = settings.rootpage + report_name + '/Configuration'

crontab = subprocess.Popen('crontab -l', stdout = subprocess.PIPE, shell = True).communicate()[0]
crontab_line = re.search('^.*' + report_filename + '.*$', crontab, re.MULTILINE).group(0)
 
template = u'''
== %s ==
<source lang="python" enclose="div">
%s
</source>

== crontab ==
<pre>
%s
</pre>
'''
 
wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)
 
configuration = wikitools.Page(wiki, configuration_title)
configuration_text = template % (report_filename, report_source, crontab_line)
configuration_text = configuration_text.encode('utf-8')
configuration.edit(configuration_text, summary=settings.editsumm if len(sys.argv) < 3 else sys.argv[2], bot=1)
