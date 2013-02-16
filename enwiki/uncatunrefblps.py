#!/usr/bin/python

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

report_title = config.get('dbreps', 'rootpage') + 'Uncategorized and unreferenced biographies of living people'

report_template = u'''
Pages in [[:Category:All unreferenced BLPs]] in need of proper categorization; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Biography
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

excluded_categories_living = [u'Living_people', u'\d+_births']
excluded_categories_living_re = re.compile(r'(%s)' % '|'.join(str(r'^%s$' % i) for i in excluded_categories_living), re.U)
excluded_categories_maintenance = []

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
for category in ['Wikipedia_maintenance', 'Hidden_categories']:
    cursor.execute('''
    /* uncatunrefblps.py SLOW_OK */
    SELECT
      page_title
    FROM page
    JOIN categorylinks
    ON cl_from = page_id
    WHERE page_namespace = 14
    AND cl_to = %s;
    ''' , category)
    for row in cursor.fetchall():
        member_category = u'%s' % unicode(row[0], 'utf-8')
        excluded_categories_maintenance.append(member_category)

cursor.execute('SET SESSION group_concat_max_len = 1000000;')
cursor.execute('''
/* uncatunrefblps.py SLOW_OK */
SELECT
  page_title,
  GROUP_CONCAT(cl2.cl_to SEPARATOR '|')
FROM page
JOIN categorylinks AS cl1
ON cl1.cl_from = page_id
LEFT JOIN categorylinks AS cl2
ON cl2.cl_from = page_id
WHERE cl1.cl_to = 'All_unreferenced_BLPs'
AND page_namespace = 0
GROUP BY page_id;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'%s' % unicode(row[0], 'utf-8')
    full_page_title = u'[[%s]]' % page_title
    cl_to = u'%s' % unicode(row[1], 'utf-8')
    legit_categories = []
    for cat in cl_to.split('|'):
        if cat not in excluded_categories_maintenance and not excluded_categories_living_re.search(cat):
            legit_categories.append(cat)
    if len(legit_categories) == 0:
        table_row = u'''| %d
| %s
|-''' % (i, full_page_title)
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
