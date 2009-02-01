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

import re
import wikipedia
import MySQLdb
import datetime

report_template = u'''
Categories that contain "(wikipedian|\\buser)", "wikiproject" and "participants", or "wikiproject" and "members"; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
%s
|}
'''

rows_per_page = 2250
report_title = 'Wikipedia:Database reports/User categories/%i'

site = wikipedia.getSite()

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* usercats.py SLOW_OK */
SELECT
  page_title
FROM page
WHERE page_namespace = 14;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[:Category:%s|]]' % unicode(row[0], 'utf-8')
    table_row = u'''|-
| %d
| %s''' % (i, page_title)
    if re.search(r'(wikipedian|\buser)', row[0], re.I|re.U) or (re.search(r'(wikiproject)', row[0], re.I|re.U) and re.search(r'(participant|members)', row[0], re.I|re.U)):
        output.append(table_row)
        i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

end = rows_per_page
page = 1
for start in range(0, len(output), rows_per_page):
    report = wikipedia.Page(site, report_title % page)
    report.put(report_template % (current_of, '\n'.join(output[start:end])), 'updated page', True, False)
    page += 1
    end += rows_per_page

cursor.close()
conn.close()

wikipedia.stopme()