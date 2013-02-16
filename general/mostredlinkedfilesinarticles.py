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
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Articles containing the most red-linked files'

report_template = u'''
Articles containing the most red-linked files (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Files
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* mostredlinkedfilesinarticles.py SLOW_OK */
SELECT
  page_title,
  COUNT(*)
FROM page
JOIN imagelinks
ON page_id = il_from
WHERE (NOT EXISTS (SELECT
                     1
                   FROM image
                   WHERE img_name = il_to))
AND (NOT EXISTS (SELECT
                   1
                 FROM commonswiki_p.page
                 WHERE page_title = CAST(il_to AS CHAR)
                 AND page_namespace = 6))
AND (NOT EXISTS (SELECT
                   1
                 FROM page
                 WHERE page_title = il_to
                 AND page_namespace = 6))
AND page_namespace = 0
GROUP BY page_title
ORDER BY COUNT(*) DESC
LIMIT 1000;
''')

i = 1
output = []
for row in cursor.fetchall():
    try:
        page_title = u'[[%s|]]' % unicode(row[0], 'utf-8')
    except UnicodeDecodeError:
        continue
    count = row[1]
    table_row = u'''|-
| %d
| %s
| %s''' % (i, page_title, count)
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
