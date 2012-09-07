#!/usr/bin/env python2.5

# Copyright 2010 bjweeks, MZMcBride

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
import math
import re
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Unprotected templates with many transclusions/%i'

report_template = u'''
Unprotected templates with many transclusions (over 500); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! Transclusions
%s
|}
'''

rows_per_page = 1000

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* unprotectedtemps.py SLOW_OK */
SELECT
  tl_title,
  COUNT(*)
FROM page
JOIN templatelinks
ON page_title = tl_title
AND page_namespace = tl_namespace
LEFT JOIN page_restrictions
ON pr_page = page_id
AND pr_level = 'sysop'
AND pr_type = 'edit'
WHERE tl_namespace = 10
AND pr_page IS NULL
GROUP BY tl_title
HAVING COUNT(*) > 500
ORDER BY COUNT(*) DESC;
''')

i = 1
output = []
for row in cursor.fetchall():
    tl_title = u'{{dbr link|1=%s}}' % unicode(row[0], 'utf-8')
    count = row[1]
    table_row = u'''|-
| %d
| %s
| %s''' % (i, tl_title, count)
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
    report.edit(report_text, summary=settings.editsumm, bot=1)
    page += 1
    end += rows_per_page

page = math.ceil(len(output) / float(rows_per_page)) + 1
while 1:
    report = wikitools.Page(wiki, report_title % page)
    report_text = settings.blankcontent
    report_text = report_text.encode('utf-8')
    if not report.exists:
        break
    report.edit(report_text, summary=settings.blanksumm, bot=1)
    page += 1

cursor.close()
conn.close()
