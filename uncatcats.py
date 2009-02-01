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

import wikipedia
import MySQLdb
import datetime

report_template = u'''
Uncategorized categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
! Length
! Members
! Last edit
! Last user
|-
%s
|}
'''

site = wikipedia.getSite()

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* uncatcats.py SLOW_OK */
SELECT
  page_title,
  page_len,
  cat_pages,
  rev_timestamp,
  rev_user_text
FROM revision
JOIN
(SELECT
   page_id,
   page_title,
   page_len,
   cat_pages
 FROM category
 RIGHT JOIN page ON cat_title = page_title
 LEFT JOIN categorylinks ON page_id = cl_from
 WHERE cl_from IS NULL
 AND page_namespace = 14
 AND page_is_redirect = 0) AS pagetmp
ON rev_page = pagetmp.page_id
AND rev_timestamp = (SELECT MAX(rev_timestamp)
                     FROM revision AS last 
                     WHERE last.rev_page = pagetmp.page_id);
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = row[0]
    if page_title:
        page_title = u'{{clh|1=%s}}' % unicode(page_title, 'utf-8')
    page_len = row[1]
    cat_pages = row[2]
    if cat_pages:
        cat_pages = cat_pages
    else:
        cat_pages = ''
    rev_timestamp = row[3]
    rev_user_text = u'%s' % unicode(row[4], 'utf-8')
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
|-''' % (i, page_title, page_len, cat_pages, rev_timestamp, rev_user_text)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikipedia.Page(site, 'Wikipedia:Database reports/Uncategorized categories')
report.put(report_template % (current_of, '\n'.join(output)), 'updated page', True, False)
cursor.close()
conn.close()

wikipedia.stopme()