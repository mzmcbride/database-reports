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

report_title = config.get('dbreps', 'rootpage') + 'Uncategorized templates'

report_template = u'''
Uncategorized template (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* uncattemps.py SLOW_OK */
SELECT
  ns_name,
  page_title
FROM page
JOIN toolserver.namespace
ON dbname = %s
AND page_namespace = ns_id
LEFT JOIN categorylinks
ON cl_from = page_id
WHERE page_namespace = 10
AND page_is_redirect = 0
AND ISNULL(cl_from)
AND page_title NOT LIKE '%%/%%'
LIMIT 1000;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    ns_name = u'%s' % unicode(row[0], 'utf-8')
    page_title = u'%s' % unicode(row[1], 'utf-8')
    full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
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
