#!/usr/bin/python

# Copyright 2009-2010 bjweeks, MZMcBride, svick

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

report_title = config.get('dbreps', 'rootpage') + 'New WikiProjects'

report_template = u'''
List of newly created WikiProject pages that are not subpages; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks"
|-
! No.
! Date
! Page
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* new_projects.py */
SELECT rc_timestamp, rc_title, page_is_redirect
FROM recentchanges
LEFT JOIN page ON rc_cur_id = page_id
WHERE rc_new = 1
AND rc_namespace = 4
AND rc_title LIKE 'WikiProject%'
AND rc_title NOT LIKE '%/%'
ORDER BY rc_timestamp DESC
''')

i = 1
output = []
for row in cursor.fetchall():
    timestamp = row[0];
    formatted_date = datetime.datetime.strptime(row[0], '%Y%m%d%H%M%S').strftime('%e %B %Y %H:%M:%S')
    date_row = '{{sort|%s|%s}}' % (timestamp, formatted_date)
    page_title = '[[Wikipedia:%s]]' % unicode(row[1], 'utf-8').replace('_', ' ')
    is_redirect = row[2]
    if is_redirect:
        page_title = "''" + page_title + "''"
    table_row = u'''| %d
| %s
| %s
|-''' % (i, date_row, page_title)
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
