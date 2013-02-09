#!/usr/bin/python

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

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Inactive users in user groups'

report_template = u'''
Users in user groups without any [[Special:Contributions|contributions]] in \
the past six months; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! Last edit
! User groups
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* inactiveuserrights.py SLOW_OK */
SELECT DISTINCT
  user_name,
  rev_timestamp,
  GROUP_CONCAT(ug_group)
FROM user
JOIN user_groups
ON ug_user = user_id
JOIN revision
ON rev_user = user_id
WHERE user_name NOT IN (SELECT
                          user_name
                        FROM user
                        JOIN user_groups
                        ON ug_user = user_id
                        WHERE ug_group IN ('sysop','bureaucrat'))
AND (SELECT
       MAX(rev_timestamp)
     FROM revision
     WHERE rev_user = user_id) < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 6 MONTH),'%Y%m%d%H%i%s')
AND rev_timestamp = (SELECT
                       MAX(rev_timestamp)
                     FROM revision
                     WHERE rev_user = user_id)
GROUP BY user_name;
''')

i = 1
output = []
for row in cursor.fetchall():
    user_name = u'[[User:%s|]]' % unicode(row[0], 'utf-8')
    rev_timestamp = u'[[Special:Contributions/%s|%s]]' % (unicode(row[0], 'utf-8'), row[1])
    user_groups = u'%s' % unicode(row[2], 'utf-8')
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, user_name, rev_timestamp, user_groups)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
