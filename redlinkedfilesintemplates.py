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

report_title = settings.rootpage + 'Templates containing red-linked files/%i'

report_template = u'''
Templates containing a red-linked file; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! File
! Transclusions
! File uses
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* redlinkedfilesintemplates.py SLOW_OK */
SELECT
  ns_name,
  page_title,
  il_to AS image_link,
  (SELECT
     COUNT(*)
   FROM templatelinks
   WHERE tl_title = page_title
   AND tl_namespace = 10) AS transclusion_count,
  (SELECT
     COUNT(*)
   FROM imagelinks
   WHERE page_id = il_from
   AND image_link = il_to) AS image_count
FROM page
JOIN toolserver.namespace
ON dbname = 'enwiki_p'
AND page_namespace = ns_id
JOIN imagelinks
ON page_id = il_from
WHERE (NOT EXISTS (SELECT
                     1
                   FROM image
                   WHERE img_name = il_to))
AND (NOT EXISTS (SELECT
                   1
                 FROM commonswiki_p.page
                 WHERE page_title = CAST(il_to AS CHAR)
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
    page_title = u'{{dbr link|1=%s:%s}}' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'))
    il_to = u'{{dbr link|1=%s}}' % unicode('File:' + row[2], 'utf-8')
    transclusion_count = row[3]
    image_count = row[4]
    table_row = u'''|-
| %d
| %s
| %s
| %s
| %s''' % (i, page_title, il_to, transclusion_count, image_count)
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
