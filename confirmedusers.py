#!/usr/bin/env python2.5

# Copyright 2009 bjweeks, MZMcBride

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

report_title = settings.rootpage + 'Autoconfirmed users in the confirmed user group'

report_template = u'''
Users in the "confirmed" user group who have passed the autoconfirmed threshold; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! Edit count
! First edit
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* confirmedusers.py SLOW_OK */
SELECT
  user_name,
  user_editcount,
  rev_timestamp
FROM user
JOIN user_groups
ON ug_user = user_id
JOIN revision
ON rev_user = user_id
AND ug_group = 'confirmed'
AND user_editcount > 9
AND (SELECT
       MIN(rev_timestamp)
     FROM revision
     WHERE rev_user = user_id) < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 4 DAY),'%Y%m%d%H%i%s')
AND rev_timestamp = (SELECT
                       MIN(rev_timestamp)
                     FROM revision
                     WHERE rev_user = user_id);
''')

i = 1
output = []
for row in cursor.fetchall():
    user_name = u'[[User:%s|]]' % unicode(row[0], 'utf-8')
    user_editcount = row[1]
    rev_timestamp = row[2]
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, user_name, user_editcount, rev_timestamp)
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
