#!/usr/bin/python

# Copyright 2008 bjweeks, valhallasw, MZMcBride

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
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Page count by namespace'

report_template = u'''
The number of pages in each [[Wikipedia:namespace|]]; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! ID
! Name
! Non-redirects
! Redirects
! Total
|-
%s
|- class="sortbottom"
! colspan="3" | Totals
! style="text-align:left;" | %d
! style="text-align:left;" | %d
! style="text-align:left;" | %d
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* nscounts.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  MAX(notredir),
  MAX(redir)
FROM (SELECT
        page.page_namespace,
        IF( page_is_redirect, COUNT(page.page_namespace), 0 ) AS redir,
        IF( page_is_redirect, 0, COUNT(page.page_namespace)) AS notredir
      FROM page
      GROUP BY page_is_redirect, page_namespace
      ORDER BY page_namespace, page_is_redirect) AS pagetmp
JOIN toolserver.namespace
ON page_namespace = ns_id
AND dbname = %s
GROUP BY page_namespace;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
ns_count_total_column = 0
ns_count_redirects_total_column = 0
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = row[1]
    if ns_name:
        ns_name = u'%s' % unicode(ns_name, 'utf-8')
    else:
        ns_name = '(Main)'
    ns_count = row[2]
    if ns_count:
        ns_count = ns_count
    else:
        ns_count = 0
    ns_count_redirects = row[3]
    if ns_count_redirects:
        ns_count_redirects = ns_count_redirects
    else:
        ns_count_redirects = 0
    ns_count_total_row = int(ns_count) + int(ns_count_redirects)
    ns_count_total_column += ns_count
    ns_count_redirects_total_column += ns_count_redirects
    ns_count_global_total = ns_count_total_column + ns_count_redirects_total_column
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
|-''' % (i, page_namespace, ns_name, ns_count, ns_count_redirects, ns_count_total_row)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output), ns_count_total_column, ns_count_redirects_total_column, ns_count_global_total)
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
