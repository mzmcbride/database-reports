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

report_title = settings.rootpage + 'Old deletion discussions'

report_template = u'''
Old deletion discussions; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Timestamp
! Category
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* olddeletiondiscussions.py SLOW_OK */
SELECT
  page_namespace,
  ns_name,
  page_title,
  cl_timestamp,
  cl_to
FROM page
JOIN toolserver.namespace
ON dbname = %s
AND page_namespace = ns_id
JOIN categorylinks
ON cl_from = page_id
WHERE cl_to IN ('Articles_for_deletion', 'Templates_for_deletion', 'Wikipedia_files_for_deletion', 'Categories_for_deletion', 'Categories_for_merging', 'Categories_for_renaming', 'Redirects_for_discussion', 'Miscellaneous_pages_for_deletion')
AND cl_timestamp < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 30 DAY),'%%Y-%%m-%%d %%H:%%i:%%s')
ORDER BY ns_name, page_title ASC;
''' , settings.dbname)

i = 1
output = []
for row in cursor.fetchall():
    page_namespace = row[0]
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    page_title = u'%s' % unicode(row[2], 'utf-8')
    cl_timestamp = row[3]
    cl_to = u'%s' % unicode(row[4], 'utf-8')
    if page_namespace != 0 and cl_to == 'Articles_for_deletion':
        continue
    if page_namespace in (6,14):
        full_page_title = u'[[:%s:%s]]' % (ns_name, page_title)
    elif page_namespace == 0:
        full_page_title = u'[[%s]]' % page_title
    else:
        full_page_title = u'[[%s:%s]]' % (ns_name, page_title)
    full_cl_to = u'[[Category:%s|%s]]' % (cl_to, cl_to)
    table_row = u'''| %d
| %s
| %s
| %s
|-''' % (i, full_page_title, cl_timestamp, full_cl_to)
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
