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

import datetime
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Semi-protected articles with excessively long expiries'

report_template = u'''
Articles that are semi-protected from editing for more than one year; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Protector
! Timestamp
! Expiry
! Reason
|-
%s
|}
'''

wiki = wikitools.Wiki()
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* excessivesemiarticles.py SLOW_OK */
SELECT
  page_is_redirect,
  page_title,
  user_name,
  logs.log_timestamp,
  pr_expiry,
  logs.log_comment
FROM page
JOIN page_restrictions ON page_id = pr_page
AND page_namespace = 0
AND pr_type = 'edit'
AND pr_level = 'autoconfirmed'
AND pr_expiry > DATE_FORMAT(DATE_ADD(NOW(),INTERVAL 1 YEAR),'%Y%m%d%H%i%s')
AND pr_expiry != 'infinity'
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
output = []
for row in cursor.fetchall():
    redirect = row[0]
    if redirect == 1:
        title = u'<i>[[%s]]</i>' % unicode(row[1], 'utf-8')
    else:
        title = u'[[%s]]' % unicode(row[1], 'utf-8')
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
    expiry = u'%s' % unicode(row[4], 'utf-8')
    comment = row[5]
    if comment:
        comment = u'<nowiki>%s</nowiki>' % unicode(comment, 'utf-8')
    else:
        comment = ''
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
|-''' % (i, title, user, timestamp, expiry, comment)
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