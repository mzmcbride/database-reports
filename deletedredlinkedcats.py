#!/usr/bin/env python2.5

# Copyright 2008 bjweeks, MZMcBride, CBM

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
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Deleted red-linked categories/%i'

report_template = u'''
Deleted red-linked categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
! Members
! Admin
! Timestamp
! Comment
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

def last_log_entry(page):
    params = {
        'action': 'query',
        'list': 'logevents',
        'lelimit': '1',
        'letitle': page,
        'format': 'json',
        'ledir': 'older',
        'letype': 'delete',
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
/* deletedredlinkedcats.py SLOW_OK */
SELECT DISTINCT
  ns_name,
  cl_to,
  cat_pages
FROM categorylinks
JOIN category
ON cl_to = cat_title
JOIN toolserver.namespace
ON dbname = 'enwiki_p'
AND ns_id = 14
LEFT JOIN page
ON cl_to = page_title
AND page_namespace = 14
WHERE page_title IS NULL
AND cat_pages > 0;
''')

i = 1
output = []
for row in cursor.fetchall():
    page = wikitools.Page(wiki, u'%s:%s' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8')), followRedir=False)
    cl_to = page.title
    cl_count = row[2]
    try:
        log_props = last_log_entry(page.title)
        user_name = log_props['user']
        log_timestamp = log_props['timestamp']
        log_comment = log_props['comment']
        if log_comment != '':
            log_comment = u'<nowiki>%s</nowiki>' % log_comment
    except:
        user_name = None
        log_timestamp = None
        log_comment = None
    if user_name is None or log_timestamp is None:
        continue
    else:
        table_row = u'''|-
| %d
| %s
| %s
| %s
| %s
| %s''' % (i, cl_to, cl_count, user_name, log_timestamp, log_comment)
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
    report.edit(report_text, summary=settings.editsumm, bot=1)
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
