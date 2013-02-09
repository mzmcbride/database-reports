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
import math
import MySQLdb
import os
import time
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Indefinitely fully protected talk pages/%i'

report_template = u'''
Talk pages that are indefinitely fully protected from editing (subpages and redirects excluded); data as of <onlyinclude>%s</onlyinclude>.

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
    try:
        timestamp = datetime.datetime.strptime(lastlog[0]['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M%S')
    except:
        timestamp = ''
    try:
        user = lastlog[0]['user']
    except:
        user = ''
    try:
        comment = lastlog[0]['comment']
    except:
        comment = ''
    return { 'timestamp': timestamp, 'user': user, 'comment': comment }


conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* indeffulltalks.py SLOW_OK */
SELECT
  page_is_redirect,
  ns_name,
  page_title
FROM page
JOIN toolserver.namespace
ON ns_id = page_namespace
AND dbname = %s
JOIN page_restrictions
ON page_id = pr_page
AND page_namespace mod 2 != 0
AND pr_type = 'edit'
AND pr_level = 'sysop'
AND pr_expiry = 'infinity'
AND page_title NOT LIKE "%%/%%"
AND page_is_redirect = 0;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    page = wikitools.Page(wiki, u'%s:%s' % (unicode(row[1], 'utf-8'), unicode(row[2], 'utf-8')), followRedir=False)
    redirect = row[0]
    namespace = row[1]
    title = row[2]
    page_title = '%s:%s' % (namespace, title)
    page_title = u'{{plh|1=%s}}' % unicode(page_title, 'utf-8')
    log_props = last_log_entry(page.title)
    user = u'[[User talk:%s|]]' % log_props['user']
    timestamp = log_props['timestamp']
    comment = u'<nowiki>%s</nowiki>' % log_props['comment']
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
        report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)
    except:
        try:
            time.sleep(3)
            report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)
        except:
            print "Man, this really sucks that it can't edit."
    page += 1
    end += rows_per_page

page = math.ceil(len(output) / float(rows_per_page)) + 1
while 1:
    report = wikitools.Page(wiki, report_title % page)
    report_text = config.get('dbreps', 'blankcontent')
    report_text = report_text.encode('utf-8')
    if not report.exists:
        break
    report.edit(report_text, summary=config.get('dbreps', 'blanksumm'), bot=1)
    page += 1

cursor.close()
conn.close()
