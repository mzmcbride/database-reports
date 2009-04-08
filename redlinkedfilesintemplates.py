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
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Templates containing red-linked files/%i'

report_template = u'''
Templates containing a red-linked file; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! File
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki()
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* redlinkedfilesintemplates.py SLOW_OK */
SELECT
  page_title,
  il_to
FROM page
JOIN imagelinks
ON page_id = il_from
WHERE (NOT EXISTS (SELECT
                     1
                   FROM image
                   WHERE img_name = il_to))
AND (NOT EXISTS (SELECT
                   1
                 FROM commonswiki_p.page
                 WHERE page_title = il_to
                 AND page_namespace = 6))
AND (NOT EXISTS (SELECT
                   1
                 FROM page
                 WHERE page_title = il_to
                 AND page_namespace = 6))
AND page_namespace = 10;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[Template:%s|]]' % unicode(row[0], 'utf-8')
    il_to = u'%s' % unicode(row[1], 'utf-8')
    table_row = u'''|-
| %d
| %s
| %s''' % (i, page_title, il_to)
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
    report.edit(report_text, summary='updated page')
    page += 1
    end += rows_per_page

cursor.close()
conn.close()