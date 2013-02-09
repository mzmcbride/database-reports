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

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Biographies of living people possibly eligible for deletion'

report_template = u'''
Biographies of living people possibly eligible for deletion. Biographies \
in [[:Category:BLP articles proposed for deletion]] or [[:Category:Articles for deletion]] \
are marked in bold. Data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Biography
! First edit
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()

categorized_pages = set()
cursor.execute('''
/* stickyprodblps.py SLOW_OK */
SELECT
  cl_from
FROM categorylinks
WHERE cl_to IN ('BLP_articles_proposed_for_deletion', 'Articles for deletion');
''')
for row in cursor.fetchall():
    categorized_pages.add(row[0])

cursor.execute('''
/* stickyprodblps.py SLOW_OK */
SELECT
  page_id,
  page_title,
  rev_timestamp
FROM page
JOIN revision
ON rev_page = page_id
JOIN categorylinks
ON cl_from = page_id
WHERE cl_to = 'All_unreferenced_BLPs'
AND page_namespace = 0
AND page_is_redirect = 0
AND rev_timestamp = (SELECT
                       MIN(rev_timestamp)
                     FROM revision AS last
                     WHERE last.rev_page = page_id)
AND rev_timestamp > '20100318000000';
''')

i = 1
output = []
for row in cursor.fetchall():
    page_id = row[0]
    if page_id in categorized_pages:
        page_title = u'<b>{{dbr link|1=%s}}</b>' % unicode(row[1], 'utf-8')
    else:
        page_title = u'{{dbr link|1=%s}}' % unicode(row[1], 'utf-8')
    rev_timestamp = row[2]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, rev_timestamp)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
