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

report_title = config.get('dbreps', 'rootpage') + 'Short single-author pages'

report_template = u'''
Templateless non-redirect pages with ten or fewer bytes and a single author; data as of <onlyinclude>%s</onlyinclude>.

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
/* shortpages.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  page_title,
  page_len
FROM page
JOIN toolserver.namespace
ON page_namespace = ns_id
AND dbname = %s
LEFT JOIN templatelinks
ON tl_from = page_id
WHERE page_is_redirect = 0
AND tl_from IS NULL
AND page_len < 11
AND page_len > 0
AND (SELECT
       COUNT(DISTINCT rev_user_text)
     FROM revision
     WHERE rev_page = page_id) = 1;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = unicode(row[1], 'utf-8')
    page_title = unicode(row[2], 'utf-8')
    page_len = row[3]
    if page_namespace in (6,14):
        page_title = u'{{plh|1=:%s:%s}}' % (ns_name, page_title)
    elif page_namespace == 0:
        page_title = u'{{plh|1=%s}}' % (page_title)
    else:
        page_title = u'{{plh|1=%s:%s}}' % (ns_name, page_title)
    if page_namespace == 8 or page_namespace == 10:
        continue
    elif page_namespace in (2,3):
        if not re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', unicode(row[2], 'utf-8'), re.I|re.U):
            continue
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
