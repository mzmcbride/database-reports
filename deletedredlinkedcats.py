#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, MZMcBride, CBM

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

report_title = settings.rootpage + 'Deleted red-linked categories/%i'

report_template = u'''
Deleted red-linked categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
! Members
! Admin
! Timestamp
! Comment
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* deletedredlinkedcats.py SLOW_OK */
SELECT
  cattmp.cl_to,
  cattmp.cl_count,
  user_name,
  log_timestamp,
  log_comment
FROM logging
JOIN user ON log_user = user_id
JOIN
(SELECT
   cl_to,
   COUNT(cl_to) AS cl_count
 FROM categorylinks
 LEFT JOIN page ON cl_to = page_title
 AND page_namespace = 14
 WHERE page_title IS NULL
 GROUP BY cl_to) AS cattmp
ON log_title = cattmp.cl_to
WHERE log_namespace = 14
AND log_type = "delete"
AND log_timestamp = (SELECT
                       MAX(log_timestamp)
                     FROM logging AS last
                     WHERE log_namespace = 14
                     AND cattmp.cl_to = last.log_title);
''')

i = 1
output = []
for row in cursor.fetchall():
    cl_to = row[0]
    if cl_to:
        cl_to = u'[[:Category:%s|]]' % unicode(cl_to, 'utf-8')
    cl_count = row[1]
    user_name = u'%s' % unicode(row[2], 'utf-8')
    log_timestamp = row[3]
    log_comment = row[4]
    if log_comment:
        log_comment = u'<nowiki>%s</nowiki>' % unicode(log_comment, 'utf-8')
    table_row = u'''|-
| %d
| %s
| %s
| %s
| %s
| %s''' % (i, cl_to, cl_count, user_name, log_timestamp, log_comment)
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

cursor.close()
conn.close()