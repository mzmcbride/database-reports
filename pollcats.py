#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, MZMcBride, CBM

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

import wikipedia
import MySQLdb
import datetime

report_template = u'''
Categories that contain pages in the (Main) namespace and the User: namespace (limited to the first 250 entries); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
|-
%s
|}
'''

site = wikipedia.getSite()

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* pollcats.py SLOW_OK */
SELECT DISTINCT
  cl_to
FROM categorylinks AS cat
JOIN page AS pg1
ON cat.cl_from = pg1.page_id
WHERE page_namespace = 2
AND EXISTS (SELECT
              1
            FROM page AS pg2
            JOIN categorylinks AS cl
            ON pg2.page_id = cl.cl_from
            WHERE pg2.page_namespace = 0
            AND cat.cl_to = cl.cl_to)
LIMIT 250;
''')

i = 1
output = []
for row in cursor.fetchall():
    cl_to = row[0]
    if cl_to:
        cl_to = u'[[:Category:%s|]]' % unicode(cl_to, 'utf-8')
    table_row = u'''| %d
| %s
|-''' % (i, cl_to)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikipedia.Page(site, 'Wikipedia:Database reports/Polluted categories')
report.put(report_template % (current_of, '\n'.join(output)), 'updated page', True, False)
cursor.close()
conn.close()

wikipedia.stopme()