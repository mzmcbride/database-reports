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

report_title = settings.rootpage + 'Orphaned single-author project pages'

report_template = u'''
Orphaned single-author project pages; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* orphanedprojs.py SLOW_OK */
SELECT DISTINCT
  ns_name,
  pg1.page_title
FROM page AS pg1
JOIN toolserver.namespace
ON dbname = 'enwiki_p'
AND pg1.page_namespace = ns_id
JOIN revision
ON rev_page = pg1.page_id
LEFT JOIN categorylinks
ON cl_from = pg1.page_id
LEFT JOIN pagelinks
ON pl_from = pg1.page_id
WHERE pg1.page_namespace = 4
AND pg1.page_is_redirect = 0
AND cl_from IS NULL
AND (SELECT
       COUNT(DISTINCT rev_user_text)
     FROM revision
     WHERE rev_page = pg1.page_id) = 1
AND (SELECT
       COUNT(*)
     FROM page AS pg2
     LEFT JOIN pagelinks AS pltmp
     ON pg2.page_id = pltmp.pl_from
     WHERE pltmp.pl_title = pg1.page_title
     AND pltmp.pl_namespace = pg1.page_namespace
     AND pg2.page_namespace = 4) = 0
AND NOT EXISTS (SELECT
                  1
                FROM templatelinks
                JOIN page AS pg3
                ON tl_from = pg3.page_id
                WHERE tl_namespace = 4
                AND tl_title = pg1.page_title
                AND pg3.page_namespace = 4);
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'{{pllh|1=%s:%s}}' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'))
    table_row = u'''| %d
| %s
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
