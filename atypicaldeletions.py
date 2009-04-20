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
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Atypical deletion log actions'

report_template = u'''
Atypical deletion log actions; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! Page
! Timestamp
! Action
! Comment
|-
%s
|}
'''

wiki = wikitools.Wiki()
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* atypicaldeletions.py SLOW_OK */
SELECT
  user_name,
  log_namespace,
  ns_name,
  log_timestamp,
  log_action,
  log_title,
  log_comment
FROM logging
JOIN toolserver.namespace
ON log_namespace = ns_id
AND dbname = 'enwiki_p'
JOIN user
ON log_user = user_id
WHERE log_type='delete'
AND log_action != 'restore'
AND log_action != 'delete';
''')

i = 1
output = []
for row in cursor.fetchall():
    user_name = u'[[User talk:%s|]]' % unicode(row[0], 'utf-8')
    log_namespace = row[1]
    ns_name = u'%s' % unicode(row[2], 'utf-8')
    log_timestamp = row[3]
    log_action = row[4]
    log_title = u'%s' % unicode(row[5], 'utf-8')
    log_comment = u'<nowiki>%s</nowiki>' % unicode(row[6], 'utf-8')
    if log_namespace == 6 or log_namespace == 14:
        log_title = '[[:%s:%s]]' % (ns_name, log_title)
    elif ns_name:
        log_title = '[[%s:%s]]' % (ns_name, log_title)
    else:
        log_title = '[[%s]]' % (log_title)
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
|-''' % (i, user_name, log_title, log_timestamp, log_action, log_comment)
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