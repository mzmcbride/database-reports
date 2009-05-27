#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, Multichil, MZMcBride

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
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Stubs included directly in stub categories/%i'

report_template = u'''
Stubs included directly in stub categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* directstubs.py SLOW_OK */
SELECT DISTINCT
  page_title
FROM page AS pgtmp
JOIN templatelinks
ON pgtmp.page_id = tl_from
JOIN categorylinks
ON pgtmp.page_id = cl_from
WHERE page_namespace = 0
AND page_is_redirect = 0
AND NOT EXISTS (SELECT
                  1
                FROM templatelinks
                WHERE pgtmp.page_id = tl_from
                AND tl_namespace = 10
                AND tl_title LIKE "%stub")
AND EXISTS (SELECT
              1
            FROM categorylinks
            WHERE pgtmp.page_id = cl_from
            AND cl_to LIKE "%stubs");
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[%s]]' % unicode(row[0], 'utf-8')
    table_row = u'''|-
| %d
| %s''' % (i, page_title)
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