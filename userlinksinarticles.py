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

report_title = settings.rootpage + 'Articles containing links to the user space'

report_template = u'''
Articles containing links to User: or User_talk: pages; data as of <onlyinclude>%s</onlyinclude>.
 
{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

skip_pages = []
conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* userlinksinarticles.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN templatelinks
ON tl_from = page_id
WHERE tl_title IN ('Db-meta', 'Under_construction')
AND tl_namespace = 10
AND page_namespace = 0;
''')
for row in cursor.fetchall():
    skip_pages.append(row[0])

cursor.execute('''
/* userlinksinarticles.py SLOW_OK */
SELECT DISTINCT
  page_title
FROM page AS pg1
JOIN pagelinks
ON pl_from = pg1.page_id
WHERE page_namespace = 0
AND EXISTS (SELECT
              1
            FROM pagelinks
            WHERE pl_from = pg1.page_id
            AND pl_namespace IN (2,3));
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'%s' % unicode(row[0], 'utf-8')
    if page_title in skip_pages:
        continue
    table_row = u'''| %d
| {{plenr|1=%s}}
|-''' % (i, page_title)
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
