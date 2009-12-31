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
import MySQLdb, MySQLdb.cursors
import re
import wikitools
import settings

report_title = settings.rootpage + 'Eponymous templates'

report_template = u'''
Eponymous templates; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
! User
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf', cursorclass=MySQLdb.cursors.SSCursor)
cursor = conn.cursor()
cursor.execute('''
/* epontemps.py SLOW_OK */
SELECT
  page_title,
  rev_user_text
FROM page
JOIN revision
ON rev_page = page_id
WHERE rev_timestamp = (SELECT
                         MIN(rev_timestamp)
                       FROM revision AS last
                       WHERE last.rev_page = page_id)
AND page_namespace = 10;
''')

i = 1
output = []
while True:
    row = cursor.fetchone()
    if row == None:
        break
    page_title = u'%s' % unicode(row[0], 'utf-8')
    rev_user_text = u'%s' % re.sub(' ', '_', unicode(row[1], 'utf-8'))
    full_page_title = u'[[Template:%s|%s]]' % (page_title, page_title)
    full_rev_user_text = u'%s' % (rev_user_text)
    table_row = u'''| %d
| %s
| %s
|-''' % (i, full_page_title, full_rev_user_text)
    if re.search(r"%s" % re.escape(rev_user_text), r"%s" % re.escape(page_title), re.I) and len(rev_user_text) > 1:
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
