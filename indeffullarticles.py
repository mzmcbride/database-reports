#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, CBM, MZMcBride

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
Articles that are indefinitely fully-protected from editing; data as of <onlyinclude>%s</onlyinclude>.

== Non-redirects ==
{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Protector
! Timestamp
! Reason
|-
%s
|}

== Redirects ==
{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Protector
! Timestamp
! Reason
|-
%s
|}
'''

site = wikipedia.getSite()

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* indeffullarticles.py SLOW_OK */
SELECT
  page_is_redirect,
  page_title,
  user_name,
  logs.log_timestamp,
  logs.log_comment
FROM page
JOIN page_restrictions ON page_id = pr_page
AND page_namespace = 0
AND pr_type = 'edit'
AND pr_level = 'sysop'
AND pr_expiry = 'infinity'
LEFT JOIN logging AS logs ON logs.log_title = page_title
                         AND logs.log_namespace = 0
                         AND logs.log_type = 'protect'
LEFT JOIN user ON logs.log_user = user_id 
WHERE CASE WHEN (NOT ISNULL(log_timestamp)) 
  THEN log_timestamp = (SELECT MAX(last.log_timestamp)
                        FROM logging AS last 
                        WHERE log_title = page_title 
                        AND log_namespace = 0
                        AND log_type = 'protect') 
  ELSE 1 END;
''')

i = 1
h = 1
output1 = []
output2 = []
for row in cursor.fetchall():
    redirect = row[0]
    title = row[1]
    user = row[2]
    if user:
        user = u'[[User talk:%s|]]' % unicode(user, 'utf-8')
    else:
        user = ''
    timestamp = row[3]
    if timestamp:
        timestamp = u'%s' % unicode(timestamp, 'utf-8')
    else:
        timestamp = ''
    comment = row[4]
    if comment:
        comment = u'<nowiki>%s</nowiki>' % unicode(comment, 'utf-8')
    else:
        comment = ''
    if redirect == 0:
        title = u'{{plh|1=%s}}' % unicode(title, 'utf-8')
        num = i
        i += 1
    else:
        title = u'{{plhnr|1=%s}}' % unicode(title, 'utf-8')
        num = h
        h += 1
    table_row = u'''| %d
| %s
| %s
| %s
| %s
|-''' % (num, title, user, timestamp, comment)
    if redirect == 0:
        output1.append(table_row)
    else:
        output2.append(table_row)

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikipedia.Page(site, 'Wikipedia:Database reports/Indefinitely fully-protected articles')
report.put(report_template % (current_of, '\n'.join(output1), '\n'.join(output2)), 'updated page', True, False)
cursor.close()
conn.close()

wikipedia.stopme()