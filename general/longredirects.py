#!/usr/bin/python

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

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Redirects obscuring page content'

report_template = u'''
Redirects whose page length is greater than 449 bytes; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Redirect
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
/* longredirects.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  page_title,
  page_len
FROM page
JOIN toolserver.namespace
ON page_namespace = ns_id
AND dbname = %s
WHERE page_is_redirect = 1
HAVING page_len > 449
ORDER BY page_namespace ASC;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    page_title = u'%s' % unicode(row[2], 'utf-8')
    if ns_name:
        page_title = '{{rle|1=%s:%s}}' % (ns_name, page_title)
    else:
        page_title = '{{rle|1=%s}}' % (page_title)
    page_len = row[3]
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
