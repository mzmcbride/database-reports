#!/usr/bin/python

# Copyright 2009-2010 bjweeks, MZMcBride, svick

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

report_title = config.get('dbreps', 'rootpage') + 'WikiProject watchers'

report_template = u'''
List of WikiProjects by number of watchers of its main page, with at least 100 of them; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks"
|-
! No.
! WikiProject
! Watchers
! Active watchers
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* project_watchers.py */
/* SLOW_OK */
SELECT
  wl_title AS project,
  COUNT(*) AS watchers,
  IFNULL(SUM(ts_wl_user_touched_cropped>NOW()-INTERVAL 30 DAY), 0) AS active
FROM watchlist
JOIN page ON page_namespace = wl_namespace
  AND page_title = wl_title
WHERE wl_title LIKE 'WikiProject\_%'
AND wl_title NOT LIKE '%/%'
AND wl_namespace = 4
GROUP BY project
HAVING watchers >= 100
ORDER BY watchers DESC
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = '[[Wikipedia:%s]]' % unicode(row[0], 'utf-8').replace('_', ' ')
    watchers = row[1]
    active_watchers = row[2]
    table_row = u'''| %d
| %s
| %d
| %d
|-''' % (i, page_title, watchers, active_watchers)
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
