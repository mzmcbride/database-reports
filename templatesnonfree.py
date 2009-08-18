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

report_title = settings.rootpage + 'Templates containing non-free files'

report_template = u'''
Templates containing non-free files; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! Non-free files
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* templatesnonfree.py SLOW_OK */
SELECT
  imgtmp.ns_name,
  imgtmp.page_title,
  COUNT(cl_to)
FROM page AS pg1
JOIN categorylinks
ON cl_from = pg1.page_id
JOIN (SELECT
        pg2.page_namespace,
        ns_name,
        pg2.page_title,
        il_to
      FROM page AS pg2
      JOIN toolserver.namespace
      ON dbname = 'enwiki_p'
      AND pg2.page_namespace = ns_id
      JOIN imagelinks
      ON il_from = page_id
      WHERE pg2.page_namespace = 10) AS imgtmp
ON il_to = pg1.page_title
WHERE pg1.page_namespace = 6
AND cl_to = 'All_non-free_media'
GROUP BY imgtmp.page_namespace, imgtmp.page_title
ORDER BY COUNT(cl_to) ASC;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[%s:%s|%s]]' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'), unicode(row[1], 'utf-8'))
    count = row[2]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, count)
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
