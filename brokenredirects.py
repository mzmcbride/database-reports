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
import re
import time
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Broken redirects'

report_template = u'''
Broken redirects; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Redirect
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* brokenredirects.py SLOW_OK */
SELECT
  p1.page_namespace,
  ns_name,
  p1.page_title
FROM redirect AS rd
JOIN page p1
ON rd.rd_from = p1.page_id
JOIN toolserver.namespace
ON p1.page_namespace = ns_id
AND dbname = %s
LEFT JOIN page AS p2
ON rd_namespace = p2.page_namespace
AND rd_title = p2.page_title
WHERE rd_namespace >= 0
AND p2.page_namespace IS NULL
ORDER BY p1.page_namespace ASC;
''' , settings.dbname)

i = 1
output = []
for row in cursor.fetchall():
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    page_title = u'%s' % unicode(row[2], 'utf-8')
    page_namespace = row[0]
    if page_namespace == 6 or page_namespace == 14:
        page_title = ':%s:%s' % (ns_name, page_title)
    elif ns_name:
        page_title = '%s:%s' % (ns_name, page_title)
    else:
        page_title = '%s' % (page_title)
    table_row = u'''|-
| %d
| [[%s]]''' % (i, page_title)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=settings.editsumm, bot=1)

cursor.close()
conn.close()
