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

report_title = config.get('dbreps', 'rootpage') + 'Unused non-free files'

report_template = u'''
Unused non-free files; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! File
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* unusednonfree.py SLOW_OK */
SELECT
  ns_name,
  page_title
FROM page
JOIN toolserver.namespace
ON dbname = %s
AND page_namespace = ns_id
JOIN categorylinks AS cl1
ON cl1.cl_from = page_id
LEFT JOIN imagelinks
ON il_to = page_title
AND page_namespace = 6
LEFT JOIN categorylinks AS cl2
ON cl2.cl_from = page_id
AND cl2.cl_to = 'All_orphaned_non-free_use_Wikipedia_files'
LEFT JOIN redirect
ON rd_title = page_title
AND rd_namespace = 6
WHERE cl1.cl_to = 'All_non-free_media'
AND il_from IS NULL
AND cl2.cl_from IS NULL
AND rd_from IS NULL
AND page_is_redirect = 0
AND page_namespace = 6;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[:%s:%s|%s]]' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'), unicode(row[1], 'utf-8'))
    table_row = u'''| %d
| %s
|-''' % (i, page_title)
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
