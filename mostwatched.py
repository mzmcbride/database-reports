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

report_title = config.get('dbreps', 'rootpage') + 'Most-watched pages'

report_template = u'''
Most-watched non-deleted pages (limited to the first 1000 entries); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! [[Wikipedia:Namespace|ID]]
! Page
! Watchers
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

def namespace_names(cursor, dbname):
    nsdict = {}
    cursor.execute('''
    /* mostwatched.py namespace_names */
    SELECT
      ns_id,
      ns_name
    FROM namespace
    WHERE dbname = %s
    AND ns_id >= 0
    ORDER BY ns_id ASC;
    ''', config.get('dbreps', 'dbname'))
    for row in cursor.fetchall():
        ns_id = str(row[0])
        ns_name = str(row[1])
        nsdict[ns_id] = ns_name
    return nsdict

conn = MySQLdb.connect(host='sql-s3', db='toolserver', read_default_file='~/.my.cnf')
cursor = conn.cursor()
nsdict = namespace_names(cursor, config.get('dbreps', 'dbname'))
cursor.close()
conn.close()

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* mostwatched.py SLOW_OK */
SELECT
  wl_namespace,
  wl_title,
  COUNT(*)
FROM watchlist
JOIN page
ON wl_namespace = page_namespace
AND wl_title = page_title
WHERE wl_namespace mod 2 = 0
AND wl_namespace >= 0
GROUP BY wl_namespace, wl_title
ORDER BY COUNT(*) DESC, wl_title ASC
LIMIT 1000;
''')

i = 1
output = []
for row in cursor.fetchall():
    ns_id = row[0]
    page_namespace = str(row[0])
    page_title = u'%s' % unicode(row[1], 'utf-8')
    if ns_id == 6 or ns_id == 14:
        page_title = '[[:%s:%s]]' % (nsdict[page_namespace], page_title)
    elif ns_id == 0:
        page_title = '[[%s]]' % (page_title)
    else:
        page_title = '[[%s:%s]]' % (nsdict[page_namespace], page_title)
    watchers = row[2]
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, page_namespace, page_title, watchers)
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
