#!/usr/bin/env python2.5

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

import datetime
import MySQLdb
import re
import wikitools
import settings

report_title = settings.rootpage + 'Blank single-author pages'

report_template = u'''
Blank pages with a single author; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* blankpages.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  page_title
FROM page
JOIN toolserver.namespace
ON page_namespace = ns_id
AND dbname = 'enwiki_p'
WHERE page_len = 0
AND (SELECT
       COUNT(DISTINCT rev_user_text)
     FROM revision
     WHERE rev_page = page_id) = 1;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = unicode(row[1], 'utf-8')
    page_title = unicode(row[2], 'utf-8')
    if page_namespace in (6,14):
        page_title = u'[[:%s:%s]]' % (ns_name, page_title)
    elif page_namespace == 0:
        page_title = u'[[%s]]' % (page_title)
    else:
        page_title = u'[[%s:%s]]' % (ns_name, page_title)
    if page_namespace == 8:
        pass
    elif page_namespace in (2,3) and not re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', page_title, re.I|re.U):
        pass
    else:
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
report.edit(report_text, summary=settings.editsumm, bot=1)

cursor.close()
conn.close()