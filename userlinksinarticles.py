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

import MySQLdb
import wikitools
import datetime
import wikitools.settings

conn1 = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor1 = conn1.cursor()
cursor1.execute('''
/* userlinksinarticles.py SLOW_OK */
SELECT
  page_title
FROM page
WHERE page_namespace = 0
AND page_is_redirect = 0;
''')

all_pages = [row[0] for row in cursor1.fetchall()]
cursor1.close()
conn1.close()

report_template = u'''
Articles containing links to User: or User_talk: pages; data as of <onlyinclude>%s</onlyinclude>.
 
{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
|-
%s
|}
'''

wiki = wikitools.Wiki()
wiki.login(wikitools.settings.username, wikitools.settings.password)
output_file = open(datetime.datetime.utcnow().strftime('/home/mzmcbride/scripts/database-reports/userlinks/output-%Y%m%d.txt'), 'a')

i = 1
output = []
step = int(wiki.limit/10)
stop = step
for start in range(0, len(all_pages), step):
    print 'Checking %d pages.' % start
    params = {
        'action': 'query',
        'prop': 'links',
        'titles': '|'.join([unicode(page.replace('_', ' '), 'utf-8').encode('ascii', 'xmlcharrefreplace') for page in all_pages[start:stop]]),
        'plnamespace': '2|3'
    }
    request = wikitools.APIRequest(wiki, params)
    query = request.query(querycontinue=False)
    page_list = query['query']['pages']
    for page in page_list.values():
        if 'links' in page:
            output_file.write(page['title'].encode('ascii', 'xmlcharrefreplace') + '\n')
            output_file.flush()
            table_row = u'| %d\n| [[%s]]\n|-' % (i, page['title'].encode('ascii', 'xmlcharrefreplace'))
            output.append(table_row)
            i += 1
    stop += step

conn2 = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor2 = conn2.cursor()
cursor2.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor2.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')
cursor2.close()
conn2.close()

report = wikitools.Page(wiki, 'Wikipedia:Database reports/Articles containing links to the user space')
report.edit(report_template % (current_of, '\n'.join(output)), summary='updated page')
output_file.close()