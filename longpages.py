#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, MZMcBride

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

import wikipedia
import MySQLdb
import datetime

report_template = u'''
Pages whose page length is greater than 150,000 bytes and whose page title does not contain "/"; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Length
|-
%s
|}
'''

site = wikipedia.getSite()

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* longpages.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  page_title,
  page_len
FROM page
JOIN toolserver.namespace
ON page_namespace = ns_id
AND dbname = 'enwiki_p'
WHERE page_len > 150000
AND page_title NOT LIKE "%/%"
ORDER BY page_namespace ASC;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    page_title = u'%s' % unicode(row[2], 'utf-8')
    if ns_name:
        page_title = '{{pler|1=%s:%s}}' % (ns_name, page_title)
    else:
        page_title = '{{pler|1=%s}}' % (page_title)
    page_len = row[3]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, page_len)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikipedia.Page(site, 'Wikipedia:Database reports/Long pages')
report.put(report_template % (current_of, '\n'.join(output)), 'updated page', True, False)
cursor.close()
conn.close()

wikipedia.stopme()