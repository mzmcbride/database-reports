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

report_title = settings.rootpage + 'Biographies of living people containing unsourced statements'

report_template = u'''
{{shortcut|WP:DR/BLP}}
Pages in [[:Category:Living people]] that [[Special:WhatLinksHere/Template:Citation needed|transclude]] \
[[Template:Citation needed]] (limited to the first 500 entries); data as of <onlyinclude>%s</onlyinclude>. \
{{NOINDEX}}

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

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* unsourcedblps.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN templatelinks
ON tl_from = page_id
JOIN categorylinks
ON cl_from = page_id
WHERE cl_to = 'Living_people'
AND tl_namespace = 10
AND tl_title = 'Citation_needed'
AND page_namespace = 0
LIMIT 500;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'{{ple|1=%s}}' % unicode(row[0], 'utf-8')
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
