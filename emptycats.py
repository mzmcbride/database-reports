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
import re
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Empty categories'

report_template = u'''
Empty categories not in [[:Category:Wikipedia category redirects]], not in [[:Category:Disambiguation categories]], and do not contain "(-importance|-class|non-article|assess|_articles_missing_|_articles_in_need_of_|_articles_undergoing_|_articles_to_be_|_articles_not_yet_|Wikipedia_featured_topics)"; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
! Length
|-
%s
|}
'''

wiki = wikitools.Wiki()
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* emptycats.py SLOW_OK */
SELECT
  page_title,
  page_len
FROM categorylinks
RIGHT JOIN page ON cl_to = page_title
WHERE page_namespace = 14
AND page_is_redirect = 0
AND cl_to IS NULL
AND NOT EXISTS (SELECT
                  1
                FROM categorylinks
                WHERE cl_from = page_id
                AND cl_to = 'Wikipedia_category_redirects')
AND NOT EXISTS (SELECT
                  1
                FROM categorylinks
                WHERE cl_from = page_id
                AND cl_to = 'Disambiguation_categories')
AND NOT EXISTS (SELECT
                  1
                FROM templatelinks
                WHERE tl_from = page_id
                AND tl_namespace = 10
                AND tl_title = 'Empty_category');
''')

i = 1
output = []
for row in cursor.fetchall():
    if not re.search(r'(-importance|-class|non-article|assess|_articles_missing_|_articles_in_need_of_|_articles_undergoing_|_articles_to_be_|_articles_not_yet_|Wikipedia_featured_topics)', row[0], re.I|re.U):
       page_title = u'{{clh|1=%s}}' % unicode(row[0], 'utf-8')
       page_len = row[1]
       table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, page_len)
       output.append(table_row)
       i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary='[[Wikipedia:Bots/Requests for approval/Basketrabbit|Bot]]: Updated page.')

cursor.close()
conn.close()