#!/usr/bin/python

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

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Indefinitely fully protected articles'

report_template = u'''
Articles that are indefinitely fully protected from editing; data as of <onlyinclude>%s</onlyinclude>.

== Non-redirects ==
{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Protector
! Timestamp
! Reason
|-
%s
|}

== Redirects ==
{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Protector
! Timestamp
! Reason
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl')); wiki.setMaxlag(-1)
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

def last_log_entry(page):
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

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* indeffullarticles.py SLOW_OK */
SELECT
  page_is_redirect,
  page_title
FROM page_restrictions
JOIN page
ON page_id = pr_page
AND page_namespace = 0
AND pr_type = 'edit'
AND pr_level = 'sysop'
AND pr_expiry = 'infinity';
''')

i = 1
h = 1
output1 = []
output2 = []
for row in cursor.fetchall():
    page = wikitools.Page(wiki, u'%s' % (unicode(row[1], 'utf-8')), followRedir=False)
    redirect = row[0]
    page_title = row[1]
    if redirect == 0:
        page_title = u'{{plth|1=%s}}' % unicode(page_title, 'utf-8')
        num = i
        i += 1
    else:
        page_title = u'{{plthnr|1=%s}}' % unicode(page_title, 'utf-8')
        num = h
        h += 1
    log_props = last_log_entry(page.title)
    user = u'[[User talk:%s|]]' % log_props['user']
    timestamp = log_props['timestamp']
    comment = u'<nowiki>%s</nowiki>' % log_props['comment']
    table_row = u'''| %d
| %s
| %s
| %s
| %s
|-''' % (num, page_title, user, timestamp, comment)
    if redirect == 0:
        output1.append(table_row)
    else:
        output2.append(table_row)

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output1), '\n'.join(output2))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
