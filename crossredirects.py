#!/usr/bin/python

# Copyright 2008 bjweeks, MZMcBride, SQL

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
import math
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Cross-namespace redirects/%i'

report_template = u'''
Cross-namespace redirects from (Main) to any other namespace; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Redirect
! Target
! Categorized?
|-
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

skip_pages = []
conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* crossredirects.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN categorylinks
ON cl_from = page_id
WHERE cl_to = 'Cross-namespace_redirects';
''')
for row in cursor.fetchall():
    skip_title = u'%s' % unicode(row[0], 'utf-8')
    skip_pages.append(skip_title)

cursor.execute('''
/* crossredirects.py SLOW_OK */
SELECT
  pt.page_namespace,
  pf.page_title,
  ns_name,
  rd_title
FROM redirect, page AS pf, page AS pt
JOIN toolserver.namespace
ON pt.page_namespace = ns_id
AND dbname = %s
WHERE pf.page_namespace = 0
AND rd_title = pt.page_title
AND rd_namespace = pt.page_namespace
AND pt.page_namespace != 0
AND rd_from = pf.page_id
AND pf.page_namespace = 0;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    page_title = u'%s' % unicode(row[1], 'utf-8')
    if page_title in skip_pages:
        categorized = 'Yes'
    else:
        categorized = 'No'
    page_title = u'{{rlw|1=%s}}' % page_title
    ns_name = u'%s' % unicode(row[2], 'utf-8')
    rd_title = u'%s' % unicode(row[3], 'utf-8')
    rd_title = '{{plnr|1=%s:%s}}' % (ns_name, rd_title)
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, page_title, rd_title, categorized)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

end = rows_per_page
page = 1
for start in range(0, len(output), rows_per_page):
    report = wikitools.Page(wiki, report_title % page)
    report_text = report_template % (current_of, '\n'.join(output[start:end]))
    report_text = report_text.encode('utf-8')
    report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)
    page += 1
    end += rows_per_page

page = math.ceil(len(output) / float(rows_per_page)) + 1
while 1:
    report = wikitools.Page(wiki, report_title % page)
    report_text = config.get('dbreps', 'blankcontent')
    report_text = report_text.encode('utf-8')
    if not report.exists:
        break
    report.edit(report_text, summary=config.get('dbreps', 'blanksumm'), bot=1)
    page += 1

cursor.close()
conn.close()
