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
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Fully protected articles with unusually long expiries'

report_template = u'''
Articles that are fully protected from editing for more than one year; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Protector
! Timestamp
! Expiry
! Reason
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

def lastLogEntry(page):
    params = {
        'action': 'query',
        'list': 'logevents',
        'lelimit': '1',
        'letitle': page,
        'format': 'json',
        'ledir': 'older',
        'letype': 'protect',
        'leprop': 'user|timestamp|comment'
    }
    request = wikitools.APIRequest(wiki, params)
    response = request.query(querycontinue=False)
    lastlog = response['query']['logevents']
    timestamp = datetime.datetime.strptime(lastlog[0]['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M%S')
    user = lastlog[0]['user']
    comment = lastlog[0]['comment']
    return { 'timestamp': timestamp, 'user': user, 'comment': comment }

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* excessivefullarticles.py SLOW_OK */
SELECT
  page_is_redirect,
  page_title,
  pr_expiry
FROM page_restrictions
JOIN page
ON page_id = pr_page
WHERE page_namespace = 0
AND pr_type = 'edit'
AND pr_level = 'sysop'
AND pr_expiry > DATE_FORMAT(DATE_ADD(NOW(),INTERVAL 1 YEAR),'%Y%m%d%H%i%s')
AND pr_expiry != 'infinity';
''')

i = 1
output = []
for row in cursor.fetchall():
    page = wikitools.Page(wiki, u'%s' % (unicode(row[1], 'utf-8')), followRedir=False)
    redirect = row[0]
    if redirect == 1:
        page_title = u'<i>[[%s]]</i>' % unicode(row[1], 'utf-8')
    else:
        page_title = u'[[%s]]' % unicode(row[1], 'utf-8')
    user = u'[[User talk:%s|]]' % lastLogEntry(page.title)['user']
    timestamp = lastLogEntry(page.title)['timestamp']
    pr_expiry = row[2]
    comment = u'<nowiki>%s</nowiki>' % lastLogEntry(page.title)['comment']
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
|-''' % (i, page_title, user, timestamp, pr_expiry, comment)
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
