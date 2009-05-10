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

report_title = settings.rootpage + 'Potential reviewer candidates'

report_template = u'''
Users with more than 1,000 edits, their first edit more than a year ago, \
and their latest edit within the past month; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! Edit count
! First edit
! Latest edit
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* reviewercandidates.py SLOW_OK */
SELECT DISTINCT
  usrtmp.user_name,
  usrtmp.user_editcount,
  usrtmp.rev_timestamp AS first_edit,
  rv1.rev_timestamp AS last_edit
FROM revision AS rv1
JOIN (SELECT
        user_id,
        user_name,
        user_editcount,
        rev_timestamp
      FROM user
      JOIN revision
      ON rev_user = user_id
      WHERE user_editcount > 1000
      AND user_id NOT IN (SELECT
                            ug_user
                          FROM user_groups
                          WHERE ug_group = "bot")
      AND user_id NOT IN (SELECT
                            ug_user
                          FROM user_groups
                          WHERE ug_group = "sysop")
      AND rev_timestamp = (SELECT
                             MIN(rev_timestamp)
                           FROM revision
                           WHERE rev_user = user_id)
      AND rev_timestamp < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 1 YEAR),'%Y%m%d%H%i%s')) AS usrtmp
ON usrtmp.user_id = rv1.rev_user
WHERE rv1.rev_timestamp = (SELECT
                             MAX(rev_timestamp)
                           FROM revision
                           WHERE rev_user = usrtmp.user_id)
AND rv1.rev_timestamp > DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 1 MONTH),'%Y%m%d%H%i%s');
''')

i = 1
output = []
for row in cursor.fetchall():
    user_name = u'%s' % unicode(row[0], 'utf-8')
    user_editcount = row[1]
    first_edit = row[2]
    last_edit = row[3]
    table_row = u'''| %d
| %s
| %s
| %s
| %s
|-''' % (i, user_name, user_editcount, first_edit, last_edit)
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