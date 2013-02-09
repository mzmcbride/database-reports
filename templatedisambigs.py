#!/usr/bin/env python2.5

# Copyright 2010 bjweeks, MZMcBride

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

report_title = settings.rootpage + 'Templates containing links to disambiguation pages'

report_template = u'''
Templates containing links to disambiguation pages (limited results); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! Disambiguation page
! Transclusions
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* templatedisambigs.py SLOW_OK */
SELECT
  pltmp.page_namespace AS template_namespace,
  pltmp.page_title AS template_title,
  pltmp.pl_namespace AS disambiguation_namespace,
  pltmp.pl_title AS disambiguation_title,
  (SELECT COUNT(*) FROM templatelinks WHERE tl_namespace = 10 AND tl_title = pltmp.page_title) AS transclusions_count
FROM (SELECT
        page_namespace,
        page_title,
        pl_namespace,
        pl_title
      FROM page
      JOIN pagelinks
      ON pl_from = page_id
      WHERE page_namespace = 10
      AND pl_namespace = 0
      LIMIT 1000000) AS pltmp
JOIN page AS pg2 /* removes red links */
ON pltmp.pl_namespace = pg2.page_namespace
AND pltmp.pl_title = pg2.page_title
WHERE EXISTS (SELECT
                1
              FROM categorylinks
              WHERE pg2.page_id = cl_from
              AND cl_to = 'All_disambiguation_pages')
ORDER BY transclusions_count DESC;
''')

i = 1
output = []
for row in cursor.fetchall():
    full_template_title = u'[[%s:%s|%s]]' % ('Template', unicode(row[1], 'utf-8'), unicode(row[1], 'utf-8'))
    full_page_title = u'[[%s]]' % (unicode(row[3], 'utf-8'))
    transclusions_count = row[4]
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, full_template_title, full_page_title, transclusions_count)
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
