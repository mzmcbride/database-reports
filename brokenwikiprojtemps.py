#!/usr/bin/env python2.5

# Copyright 2011 bjweeks, MZMcBride

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

report_title = settings.rootpage + 'Broken WikiProject templates'

report_template = u'''
Broken WikiProject templates; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! Transclusions
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* brokenwikiprojtemps.py SLOW_OK */
SELECT
  tl_title,
  COUNT(*)
FROM templatelinks
JOIN page AS p1
ON tl_from = p1.page_id
LEFT JOIN page AS p2
ON tl_namespace = p2.page_namespace
AND tl_title = p2.page_title
WHERE tl_namespace = 10
AND tl_title LIKE 'Wiki%'
AND tl_title RLIKE 'Wiki[_]?[Pp]roject.*'
AND tl_title NOT LIKE '%/importance'
AND tl_title NOT LIKE '%/class'
AND p2.page_id IS NULL
GROUP BY tl_title;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'{{dbr link|1=%s}}' % unicode(row[0], 'utf-8')
    transclusions = row[1]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, transclusions)
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
