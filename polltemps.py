#!/usr/bin/env python2.5

# Copyright 2011 bjweeks, MZMcBride, WOSlinker

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

report_title = config.get('dbreps', 'rootpage') + 'Template categories containing articles'

report_template = u'''
Template categories containing articles; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* polltemps.py SLOW_OK */
SELECT
  ns_name,
  page_title
FROM page AS pg1
JOIN toolserver.namespace
ON dbname = %s
AND pg1.page_namespace = ns_id
JOIN templatelinks AS tl
ON pg1.page_id = tl.tl_from
WHERE pg1.page_namespace = 14
AND tl.tl_namespace = 10
AND tl.tl_title = 'Template_category'
AND EXISTS (SELECT
              1
            FROM page AS pg2
            JOIN categorylinks AS cl
            ON pg2.page_id = cl.cl_from
            WHERE pg2.page_namespace = 0
            AND pg1.page_title = cl.cl_to);
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    ns_name = unicode(row[0], 'utf-8')
    cl_to = unicode(row[1], 'utf-8')
    category_link = u'[[:%s:%s|%s]]' % (ns_name, cl_to, cl_to)
    table_row = u'''| %d
| %s
|-''' % (i, category_link)
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
