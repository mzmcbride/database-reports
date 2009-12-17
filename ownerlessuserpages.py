#!/usr/bin/env python2.5

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

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Ownerless pages in the user space'

report_template = u'''
Pages in the user space that do not belong to a [[Special:ListUsers|registered user]]; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Length
! Creator
! Creation date
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* ownerlessuserpages.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  page_title,
  page_len,
  rev_user_text,
  rev_timestamp
FROM revision
JOIN (SELECT
        page_id,
        page_namespace,
        page_title,
        page_len
      FROM page
      LEFT JOIN user
      ON user_name = REPLACE(SUBSTRING_INDEX(page_title, '/', 1), '_', ' ')
      WHERE page_namespace IN (2,3)
      AND page_is_redirect = 0
      AND page_title NOT RLIKE '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
      AND ISNULL(user_name)) AS pgtmp
ON pgtmp.page_id = rev_page
JOIN toolserver.namespace
ON pgtmp.page_namespace = ns_id
AND dbname = %s
AND rev_timestamp = (SELECT
                       MIN(rev_timestamp)
                     FROM revision
                     WHERE rev_page = pgtmp.page_id);
''' , settings.dbname)

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    page_title = u'[[%s:%s]]' % (ns_name, unicode(row[2], 'utf-8'))
    page_len = row[3]
    rev_user_text = u'%s' % unicode(row[4], 'utf-8')
    rev_timestamp = row[5]
    table_row = u'''| %d
| %s
| %s
| %s
| %s
|-''' % (i, page_title, page_len, rev_user_text, rev_timestamp)
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
