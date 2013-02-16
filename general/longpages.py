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

report_title = config.get('dbreps', 'rootpage') + 'Long pages'

report_template = u'''
Long pages; data as of <onlyinclude>%s</onlyinclude>.

== Specified talk pages ==
Talk pages whose page length is greater than 140,000 bytes \
(excluding subpages and pages in the user space).

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Length
! Last edit
|-
%s
|}

== All pages ==
All pages whose page length is greater than 500,000 bytes.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Length
! Last edit
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* longpages.py SLOW_OK */
SELECT
  ns_name,
  page_title,
  page_len,
  rev_timestamp
FROM page
JOIN toolserver.namespace
ON page_namespace = ns_id
AND dbname = %s
JOIN revision
ON rev_page = page_id
WHERE page_len > 140000
AND page_title NOT LIKE "%%/%%"
AND page_namespace != 3
AND page_namespace mod 2 != 0
AND rev_timestamp = (SELECT
                       MAX(rev_timestamp)
                     FROM revision
                     WHERE rev_page = page_id)
ORDER BY page_len, page_namespace ASC;
''' , config.get('dbreps', 'dbname'))

i = 1
output1 = []
for row in cursor.fetchall():
    ns_name = u'%s' % unicode(row[0], 'utf-8')
    page_title = u'%s' % unicode(row[1], 'utf-8')
    if ns_name:
        page_title = '{{dbr link|1=%s:%s}}' % (ns_name, page_title)
    else:
        page_title = '{{dbr link|1=%s}}' % (page_title)
    page_len = row[2]
    rev_timestamp = row[3]
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, page_title, page_len, rev_timestamp)
    output1.append(table_row)
    i += 1

cursor.execute('''
/* longpages.py SLOW_OK */
SELECT
  ns_name,
  page_title,
  page_len,
  rev_timestamp
FROM page
JOIN toolserver.namespace
ON page_namespace = ns_id
AND dbname = %s
JOIN revision
ON rev_page = page_id
WHERE page_len > 500000
AND rev_timestamp = (SELECT
                       MAX(rev_timestamp)
                     FROM revision
                     WHERE rev_page = page_id)
ORDER BY page_len, page_namespace ASC;
''' , config.get('dbreps', 'dbname'))

i = 1
output2 = []
for row in cursor.fetchall():
    ns_name = u'%s' % unicode(row[0], 'utf-8')
    page_title = u'%s' % unicode(row[1], 'utf-8')
    if ns_name:
        page_title = '{{dbr link|1=%s:%s}}' % (ns_name, page_title)
    else:
        page_title = '{{dbr link|1=%s}}' % (page_title)
    page_len = row[2]
    rev_timestamp = row[3]
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, page_title, page_len, rev_timestamp)
    output2.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output1), '\n'.join(output2))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
