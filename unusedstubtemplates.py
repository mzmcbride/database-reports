#!/usr/bin/env python2.5

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

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Unused stub templates'

report_template = u'''
Unused stub templates; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! Last edit
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* unusedstubtemplates.py SLOW_OK */
SELECT
  ns_name,
  page_title,
  rev_timestamp
FROM page
JOIN toolserver.namespace
ON dbname = %s
AND page_namespace = ns_id
LEFT JOIN templatelinks
ON page_namespace = tl_namespace
AND page_title = tl_title
JOIN revision
ON rev_page = page_id
WHERE page_namespace = 10
AND page_is_redirect = 0
AND page_title LIKE '%%-stub'
AND tl_from IS NULL
AND rev_timestamp = (SELECT
                       MAX(rev_timestamp)
                     FROM revision
                     WHERE rev_page = page_id);
''' , settings.dbname)

i = 1
output = []
for row in cursor.fetchall():
    ns_name = u'%s' % unicode(row[0], 'utf-8')
    page_title = u'%s' % unicode(row[1], 'utf-8')
    full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
    rev_timestamp = row[2]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, full_page_title, rev_timestamp)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=settings.editsumm, bot=1)

cursor.close()
conn.close()
