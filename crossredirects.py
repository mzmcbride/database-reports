#!/usr/bin/env python2.5

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

import datetime
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Cross-namespace redirects'

report_template = u'''
Cross-namespace redirects from (Main) to any other namespace; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Redirect
! Target
|-
%s
|}
'''

wiki = wikitools.Wiki()
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
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
AND dbname = 'enwiki_p'
WHERE pf.page_namespace = 0
AND rd_title = pt.page_title
AND rd_namespace = pt.page_namespace
AND pt.page_namespace != 0
AND rd_from = pf.page_id
AND pf.page_namespace = 0;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    page_title = u'{{rlw|1=%s}}' % unicode(row[1], 'utf-8')
    ns_name = u'%s' % unicode(row[2], 'utf-8')
    rd_title = u'%s' % unicode(row[3], 'utf-8')
    if page_namespace == 6 or page_namespace == 14:
        rd_title = '[[:%s:%s]]' % (ns_name, rd_title)
    elif ns_name:
        rd_title = '[[%s:%s]]' % (ns_name, rd_title)
    else:
        rd_title = '[[%s]]' % (rd_title)
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, rd_title)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary='[[Wikipedia:Bots/Requests for approval/Basketrabbit|Bot]]: Updated page.')

cursor.close()
conn.close()