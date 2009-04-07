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
import re
import time
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Orphaned talk pages'

report_template = u'''
Orphaned talk pages; data as of <onlyinclude>%s</onlyinclude>.

Colored rows have been checked and can be deleted without review. Pages transcluding \
{{[[Template:Go away|Go away]]}} or {{[[Template:G8-exempt|G8-exempt]]}} have been excluded.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
%s
|}
'''

delete = False
sleep_time = 0

wiki = wikitools.Wiki()
wiki.login(settings.userwhip, settings.passwhip)

def hasNoRecentRevs(talkpage):
    params = {
        'action': 'query', 
        'titles': '%s' % talkpage, 
        'prop': 'revisions', 
        'rvprop': 'timestamp', 
        'format': 'json', 
        'rvlimit': '1'
    }
    request = wikitools.APIRequest(wiki, params)
    response = request.query(querycontinue=False)
    query = response['query']['pages'].values()[0]
    if 'missing' in query:
        return True
    timestamp = datetime.datetime.strptime(query['revisions'][0]['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
    return datetime.datetime.utcnow() - timestamp > datetime.timedelta(days=7)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* orphanedtalks.py SLOW_OK */
SELECT
  p1.page_namespace,
  ns_name,
  p1.page_title
FROM page AS p1
JOIN toolserver.namespace
ON p1.page_namespace = ns_id
AND dbname = 'enwiki_p'
WHERE p1.page_title NOT LIKE "%/%"
AND p1.page_namespace NOT IN (0,2,3,4,6,8,9,10,12,14,16,18,100,102,104)
AND CASE WHEN p1.page_namespace = 1
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 0
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 5
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 4
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 7
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 6
                   AND p1.page_title = p2.page_title)
  AND NOT EXISTS (SELECT
                    1
                  FROM commonswiki_p.page AS p2
                  WHERE p2.page_namespace = 6
                  AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 11
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 10
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 13
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 12
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 15
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 14
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 17
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 16
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND CASE WHEN p1.page_namespace = 101
  THEN NOT EXISTS (SELECT
                     1
                   FROM page AS p2
                   WHERE p2.page_namespace = 100
                   AND p1.page_title = p2.page_title)
  ELSE 1 END
AND p1.page_id NOT IN (SELECT
                         page_id
                       FROM page
                       JOIN templatelinks
                       ON page_id = tl_from
                       WHERE tl_title="G8-exempt"
                       AND tl_namespace = 10)
AND p1.page_id NOT IN (SELECT
                         page_id
                       FROM page
                       JOIN templatelinks
                       ON page_id = tl_from
                       WHERE tl_title="Go_away"
                       AND tl_namespace = 10);
''')

i = 1
output = []
for row in cursor.fetchall():
    talkpage = wikitools.Page(wiki, u'%s:%s' % (unicode(row[1], 'utf-8'), unicode(row[2], 'utf-8')), followRedir=False)
    page_namespace = row[0]
    ns_name = u'%s' % unicode(row[1], 'utf-8')
    page_title = u'%s' % unicode(row[2], 'utf-8')
    if page_namespace == 6 or page_namespace == 14:
        page_title = ':%s:%s' % (ns_name, page_title)
    elif ns_name:
        page_title = '%s:%s' % (ns_name, page_title)
    else:
        page_title = '%s' % (page_title)

    if re.search(r'\\', row[2], re.I|re.U) or re.search(r'(archive|^Image:|^Image_talk:|^File:|^File_talk:|^Category:|^User:|^User_talk:|^Template:|^Talk:Talk:)', row[2], re.I|re.U):
        pass

    elif talkpage.exists and hasNoRecentRevs(talkpage.title):
        try:
            if delete:
                talkpage.delete('[[WP:CSD#G8|CSD G8]]', followRedir=False)
                time.sleep(sleep_time)
                continue
            else:
                table_row = u'''|- style="background:#EBE3F4;"
| %d
| {{plnr|1=%s}} {{ddot|1=%s}}''' % (i, page_title, page_title)
                output.append(table_row)
                i += 1
                continue
        except:
            print 'Skipped [[en:%s]]: had unknown issues' % talkpage.title()
            continue
    table_row = u'''|-
| %d
| {{plnr|1=%s}}''' % (i, page_title)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary='[[Wikipedia:Bots/Requests for approval/Whip, dip, and slide|Bot]]: Updated page.')

cursor.close()
conn.close()