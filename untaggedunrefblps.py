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

import ConfigParser
import datetime
import MySQLdb
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Untagged and unreferenced biographies of living people'

report_template = u'''
Pages in [[:Category:All unreferenced BLPs]] missing WikiProject tags; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Biography
! Categories
|-
%s
|}
'''

excluded_categories_re = re.compile(r'(\d{1,4}_births|living_people|all_unreferenced_blps|unreferenced_blps_from)', re.I)

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* untaggedunrefblps.py SLOW_OK */
SELECT
  p1.page_title,
  GROUP_CONCAT(cl2.cl_to SEPARATOR '|')
FROM page AS p1
JOIN categorylinks AS cl1
ON cl1.cl_from = p1.page_id
JOIN categorylinks AS cl2
ON cl2.cl_from = p1.page_id
WHERE cl1.cl_to = 'All_unreferenced_BLPs'
AND p1.page_namespace = 0
AND NOT EXISTS (SELECT
                  1
                FROM page AS p2
                WHERE p2.page_title = p1.page_title
                AND p2.page_namespace = 1)
GROUP BY p1.page_id;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'{{plat|1=%s}}' % unicode(row[0], 'utf-8')
    categories = u'%s' % unicode(row[1], 'utf-8')
    category_col = []
    for category in categories.split('|'):
        if not excluded_categories_re.search(category):
            category_col.append(u'[[:Category:%s|%s]]' % (category, category))
    category_links = u'%s' % ', '.join(category_col)
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, category_links)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
