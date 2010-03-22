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
import wikitools
import settings

report_title = settings.rootpage + 'Orphaned talk subpages'

report_template = u'''
Talk pages that don't have a root page and do not have a corresponding \
subject-space page; data as of <onlyinclude>%s</onlyinclude>.

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

def check_root_page_existence(cursor, page_namespace, raw_page_title):
    raw_page_title = raw_page_title.rsplit('/', 1)[0]
    cursor.execute('SELECT 1 FROM page WHERE page_namespace = %s AND page_title = %s;' , (page_namespace, raw_page_title))
    try:
        result = cursor.fetchone()[0]
        if result is not None:
            return True
    except TypeError:
        return False

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* orphanedsubtalks.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  pg1.page_title
FROM page AS pg1
JOIN toolserver.namespace
ON dbname = %s
AND page_namespace = ns_id
WHERE pg1.page_title LIKE '%%/%%'
AND pg1.page_namespace IN (1,5,7,9,11,13,101)
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg2
                WHERE pg2.page_namespace = pg1.page_namespace
                AND pg2.page_title = SUBSTRING_INDEX(pg1.page_title, '/', 1))
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg3
                WHERE pg3.page_namespace = pg1.page_namespace - 1
                AND pg3.page_title = pg1.page_title)
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg4
                WHERE pg4.page_namespace = pg1.page_namespace - 1
                AND pg4.page_title = SUBSTRING_INDEX(pg1.page_title, '/', 1));
''' , settings.dbname)

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    raw_page_title = row[2]
    page_title = u'%s' % unicode(row[2], 'utf-8')
    if check_root_page_existence(cursor, page_namespace, raw_page_title) is True:
        continue
    full_page_title = u'[[%s:%s]]' % (ns_name, page_title)
    table_row = u'''| %d
| %s
|-''' % (i, full_page_title)
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
