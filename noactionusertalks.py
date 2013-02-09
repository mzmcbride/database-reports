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
import MySQLdb, MySQLdb.cursors
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'User talk pages for inactive IPs'

report_template = u'''
User talk pages of anonymous users without any contributions (live or deleted), \
blocks, or abuse filter matches (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

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

blocks = set()
abuse_filter_matches = set()

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf', cursorclass=MySQLdb.cursors.SSCursor)
cursor = conn.cursor()
cursor.execute('''
/* noactionusertalks.py SLOW_OK */
SELECT
  log_title
FROM logging
WHERE log_type = 'block'
AND log_namespace = 2
AND log_title RLIKE %s;
''' , r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')

while True:
    row = cursor.fetchone()
    if row == None:
        break
    log_title = row[0]
    blocks.add(log_title)

cursor.execute('''
/* noactionusertalks.py SLOW_OK */
SELECT
  afl_user_text
FROM abuse_filter_log
WHERE afl_user_text RLIKE %s;
''' , r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')

while True:
    row = cursor.fetchone()
    if row == None:
        break
    afl_user_text = row[0]
    abuse_filter_matches.add(afl_user_text)

cursor.execute('''
/* noactionusertalks.py SLOW_OK */
SELECT
  ns_name,
  page_title,
  page_len
FROM page
LEFT JOIN revision
ON rev_user_text = page_title
LEFT JOIN archive
ON ar_user_text = page_title
JOIN toolserver.namespace
ON ns_id = page_namespace
AND dbname = %s
WHERE page_namespace = 3
AND ISNULL(rev_user_text)
AND ISNULL(ar_user_text)
AND page_title RLIKE %s;
''' , (config.get('dbreps', 'dbname'), r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'))

i = 1
output = []
for row in cursor.fetchall():
    if i > 1000:
        break
    ns_name = u'%s' % unicode(row[0], 'utf-8')
    page_title = u'%s' % unicode(row[1], 'utf-8')
    full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
    page_len = row[2]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, full_page_title, page_len)
    if page_title not in blocks and page_title not in abuse_filter_matches:
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
