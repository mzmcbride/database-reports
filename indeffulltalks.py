#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, CBM, MZMcBride

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
import math
import time
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Indefinitely fully-protected talk pages/%i'

report_template = u'''
Talk pages that are indefinitely fully-protected from editing (subpages and redirects excluded); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Protector
! Timestamp
! Reason
|-
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* indeffulltalks.py SLOW_OK */
SELECT
  page_is_redirect,
  ns_name,
  page_title,
  user_name,
  logs.log_timestamp,
  logs.log_comment
FROM page
JOIN toolserver.namespace
ON ns_id = page_namespace
AND dbname = 'enwiki_p'
JOIN page_restrictions
ON page_id = pr_page
AND page_namespace mod 2 != 0
AND pr_type = 'edit'
AND pr_level = 'sysop'
AND pr_expiry = 'infinity'
LEFT JOIN logging AS logs ON logs.log_title = page_title
                         AND logs.log_namespace = page_namespace
                         AND logs.log_type = 'protect'
LEFT JOIN user ON logs.log_user = user_id 
WHERE CASE WHEN (NOT ISNULL(log_timestamp)) 
  THEN log_timestamp = (SELECT
                          MAX(last.log_timestamp)
                        FROM logging AS last 
                        WHERE log_title = page_title 
                        AND log_namespace = page_namespace
                        AND log_type = 'protect') 
  ELSE 1 END
AND page_title NOT LIKE "%/%"
AND page_is_redirect = 0;
''')

i = 1
output = []
for row in cursor.fetchall():
    redirect = row[0]
    namespace = row[1]
    title = row[2]
    page_title = '%s:%s' % (namespace, title)
    user = row[3]
    if user:
        user = u'[[User talk:%s|]]' % unicode(user, 'utf-8')
    else:
        user = ''
    timestamp = row[4]
    if timestamp:
        timestamp = u'%s' % unicode(timestamp, 'utf-8')
    else:
        timestamp = ''
    comment = row[5]
    if comment:
        comment = u'<nowiki>%s</nowiki>' % unicode(comment, 'utf-8')
    else:
        comment = ''
    page_title = u'{{plh|1=%s}}' % unicode(page_title, 'utf-8')
    table_row = u'''| %d
| %s
| %s
| %s
| %s
|-''' % (i, page_title, user, timestamp, comment)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

end = rows_per_page
page = 1
for start in range(0, len(output), rows_per_page):
    report = wikitools.Page(wiki, report_title % page)
    report_text = report_template % (current_of, '\n'.join(output[start:end]))
    report_text = report_text.encode('utf-8')
    try:
        report.edit(report_text, summary=settings.editsumm, bot=1)
    except:
        try:
            time.sleep(3)
            report.edit(report_text, summary=settings.editsumm, bot=1)
        except:
            print "Man, this really sucks that it can't edit."
    page += 1
    end += rows_per_page

page = math.ceil(len(output) / float(rows_per_page)) + 1
while 1:
    report = wikitools.Page(wiki, report_title % page)
    report_text = settings.blankcontent
    report_text = report_text.encode('utf-8')
    if not report.exists:
        break
    report.edit(report_text, summary=settings.blanksumm, bot=1)
    page += 1

cursor.close()
conn.close()