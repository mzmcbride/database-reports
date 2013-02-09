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
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'File description pages containing no templates'

report_template = u'''
File description pages containing no templates (limited to the first 800 \
entries); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Length
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* templatelessfilepages.py SLOW_OK */
SELECT
  ns_name,
  pg1.page_title,
  pg1.page_len
FROM page AS pg1
JOIN toolserver.namespace
ON dbname = %s
AND ns_id = pg1.page_namespace
LEFT JOIN templatelinks
ON tl_from = pg1.page_id
WHERE NOT EXISTS (SELECT
                    img_name
                  FROM commonswiki_p.image
                  WHERE img_name = CAST(pg1.page_title AS CHAR))
AND NOT EXISTS (SELECT
                  1
                FROM commonswiki_p.page AS pg2
                WHERE pg2.page_namespace = 6
                AND pg2.page_title = CAST(pg1.page_title AS CHAR)
                AND pg2.page_is_redirect = 1)
AND pg1.page_namespace = 6
AND pg1.page_is_redirect = 0
AND tl_from IS NULL
LIMIT 800;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[:%s:%s|]]' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'))
    page_len = row[2]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, page_len)
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
