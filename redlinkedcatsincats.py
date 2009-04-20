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

import datetime
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Categories categorized in red-linked categories/%i'

report_template = u'''
Categories categorized in red-linked categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
! Member category
|-
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki()
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* redlinkedcatsincats.py SLOW_OK */
SELECT
  page_title,
  cl_to
FROM page
JOIN
(SELECT
   cl_to,
   cl_from
 FROM categorylinks
 LEFT JOIN page ON cl_to = page_title
 AND page_namespace = 14
 WHERE page_title IS NULL) AS cattmp
ON cattmp.cl_from = page_id
WHERE page_namespace = 14;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = row[0]
    if page_title:
        page_title = u'{{clh|1=%s}}' % unicode(page_title, 'utf-8')
    cl_to = row[1]
    if cl_to:
        cl_to = u'[[:Category:%s|]]' % unicode(cl_to, 'utf-8')
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, cl_to)
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
    report.edit(report_text, summary='[[Wikipedia:Bots/Requests for approval/Basketrabbit|Bot]]: Updated page.')
    page += 1
    end += rows_per_page

cursor.close()
conn.close()