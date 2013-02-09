#!/usr/bin/python

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

import ConfigParser
import datetime
import MySQLdb
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Potential biographies of dead people (2)'

report_template = u'''
Articles in [[:Category:Living people]] that are not in [[:Category:Possibly \
living people]] and are in a "XXXX deaths" category; data as of <onlyinclude>%s</onlyinclude>.

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

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* potenshbdps2.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN categorylinks
ON cl_from = page_id
WHERE cl_to = 'Living_people'
AND NOT EXISTS (SELECT
                  1
                FROM categorylinks AS cl2
                WHERE cl2.cl_from = page_id
                AND cl2.cl_to = 'Possibly_living_people')
AND EXISTS (SELECT
              1
            FROM categorylinks AS cl3
            WHERE cl3.cl_from = page_id
            AND cl3.cl_to RLIKE '^[0-9]{4}_deaths$')
AND page_namespace = 0
AND page_is_redirect = 0;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = re.sub('_', ' ', u'%s' % unicode(row[0], 'utf-8'))
    table_row = u'''| %d
| [[%s]]
|-''' % (i, page_title)
    if re.search(r'(&|\band\b|\bbrothers\b|\bsisters\b|\bquintuplets\b)', page_title):
        continue
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
