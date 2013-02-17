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

report_title = config.get('dbreps', 'rootpage') + 'Redirects containing red links'

report_template = u'''
Redirects containing red links (limited to the first 800 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Redirect
! Red links
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('SET SESSION group_concat_max_len = 1000000;')
cursor.execute('''
/* redreds.py SLOW_OK */
SELECT
  ns1.ns_name,
  pg2.page_title,
  GROUP_CONCAT(CONCAT(ns2.ns_name,':',pl_title))
FROM pagelinks
LEFT JOIN page AS pg1
ON pl_namespace = pg1.page_namespace
AND pl_title = pg1.page_title
LEFT JOIN page AS pg2
ON pl_from = pg2.page_id
JOIN toolserver.namespace AS ns1
ON ns1.dbname = %s
AND ns1.ns_id = pg2.page_namespace
JOIN toolserver.namespace AS ns2
ON ns2.dbname = %s
AND ns2.ns_id = pl_namespace
WHERE pg1.page_namespace IS NULL
AND pg2.page_is_redirect = 1
GROUP BY pg2.page_namespace, pg2.page_title
LIMIT 800;
''' , (config.get('dbreps', 'dbname'), config.get('dbreps', 'dbname')))

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'{{plnr|1=%s:%s}}' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'))
    red_links = unicode(row[2], 'utf-8')
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, red_links)
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
