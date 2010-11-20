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
 
report_title = settings.rootpage + 'Talk pages by size'
 
report_template = u'''
List of talk pages by their total size, including subpages; \
data as of <onlyinclude>%s</onlyinclude>.
 
{| class="wikitable sortable plainlinks"
|-
! No.
! Page
! Size [kB]
|-
%s
|}
'''
 
wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)
 
conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* longest_discussions.py */
SELECT 
	ns_name,
	REPLACE(SUBSTRING_INDEX(page_title, '/', 1), '_', ' ') AS parent,
	SUM(page_len) / 1024 AS total_size
FROM page
  JOIN toolserver.namespacename ON page_namespace = ns_id 
WHERE page_namespace MOD 2 = 1
  AND dbname = 'enwiki_p'
  AND ns_type = 'primary'
GROUP BY page_namespace, parent
ORDER BY total_size DESC
LIMIT 300
''')
 
i = 1
output = []
for row in cursor.fetchall():
    page_title = '[[%s:%s]]' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'))
    size = row[2]
    table_row = u'''| %d
| %s
| %d
|-''' % (i, page_title, size)
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
