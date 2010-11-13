#!/usr/bin/env python2.5
 
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
 
import datetime
import MySQLdb
import wikitools
import settings
 
report_title = settings.rootpage + 'WikiProjects by changes'
 
report_template = u'''
List of WikiProjects by number of changes to all its pages in the last 30 days; \
data as of <onlyinclude>%s</onlyinclude>.
 
{| class="wikitable sortable plainlinks"
|-
! No.
! WikiProject
! Edits
|-
%s
|}
'''
 
wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)
 
conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* project_changes.py */
SELECT REPLACE(SUBSTRING_INDEX(rc_title, '/', 1), '_', ' ') AS project, COUNT(*) AS count
FROM recentchanges
WHERE rc_title LIKE 'WikiProject\_%'
AND rc_namespace BETWEEN 4 AND 5
GROUP BY project
ORDER BY count DESC
''')
 
i = 1
output = []
for row in cursor.fetchall():
    page_title = '[[Wikipedia:%s]]' % unicode(row[0], 'utf-8')
    edits = row[1]
    table_row = u'''| %d
| %s
| %d
|-''' % (i, page_title, edits)
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
