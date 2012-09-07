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

report_title = settings.rootpage + 'Blocked users in user groups'

report_template = u'''
Users in user groups who are currently blocked; data as of \
<onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! User groups
! Blocker
! Expiry
! Reason
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* blockeduserrights.py SLOW_OK */
SELECT
  user_name,
  ug_group,
  ipb_by_text,
  ipb_expiry,
  ipb_reason
FROM user
JOIN ipblocks
ON user_id = ipb_user
JOIN user_groups
ON user_id = ug_user;
''')

i = 1
output = []
for row in cursor.fetchall():
    user_name = u'[[User:%s|]]' % unicode(row[0], 'utf-8')
    user_groups = u'%s' % unicode(row[1], 'utf-8')
    ipb_by_text = u'[[User talk:%s|]]' % unicode(row[2], 'utf-8')
    ipb_expiry = u'%s' % unicode(row[3], 'utf-8')
    ipb_reason = u'<nowiki>%s</nowiki>' % unicode(row[4], 'utf-8')
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
|-''' % (i, user_name, user_groups, ipb_by_text, ipb_expiry, ipb_reason)
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
