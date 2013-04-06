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

report_title = config.get('dbreps', 'rootpage') + 'WikiProjects by changes'

report_template = u'''
List of WikiProjects by number of changes to all its pages in the last 365 days; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks"
|-
! No.
! WikiProject
! Edits
! excl. bots
|-
%s
|}

[[pl:Wikipedysta:Svick/WikiProjects by changes]]
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* project_changes.py */
/* SLOW_OK */
SELECT SUBSTRING_INDEX(page_title, '/', 1) AS project,
       SUM((
         SELECT COUNT(*)
         FROM revision
         WHERE page_id = rev_page
         AND DATEDIFF(NOW(), rev_timestamp) <= 365
       )) AS count,
       SUM((
         SELECT COUNT(*)
         FROM revision
         WHERE page_id = rev_page
         AND DATEDIFF(NOW(), rev_timestamp) <= 365
         AND rev_user NOT IN
          (SELECT ug_user
          FROM user_groups
          WHERE ug_group = 'bot')
       )) AS no_bots_count,
       (SELECT page_is_redirect
       FROM page
       WHERE page_namespace = 4
       AND page_title = project) AS redirect
FROM page
WHERE (page_title LIKE 'WikiProject\_%'
  OR page_title LIKE 'WikiAfrica')
AND page_namespace BETWEEN 4 AND 5
AND page_is_redirect = 0
GROUP BY project
ORDER BY count DESC
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = '[[Wikipedia:%s]]' % unicode(row[0], 'utf-8').replace('_', ' ')
    edits = row[1]
    no_bots_edits = row[2]
    is_redirect = row[3]
    if is_redirect:
        page_title = "''" + page_title + "''"
    table_row = u'''| %d
| %s
| %d
| %d
|-''' % (i, page_title, edits, no_bots_edits)
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
