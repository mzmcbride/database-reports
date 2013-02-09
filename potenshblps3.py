#!/usr/bin/python

# Copyright 2009 bjweeks, MZMcBride

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
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Potential biographies of living people (3)'

report_template = u'''
Articles whose talk pages transclude {{tl|BLP}} that are likely to be biographies \
of living people, but are not in [[:Category:Living people]], [[:Category:Possibly \
living people]], or [[:Category:Missing people]] (limited to the first 1000 \
entries); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Biography
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* potenshblps3.py SLOW_OK */
SELECT
  pg1.page_title
FROM page AS pg1
JOIN templatelinks
ON pg1.page_id = tl_from
WHERE tl_namespace = 10
AND tl_title = 'BLP'
AND pg1.page_namespace = 1
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg2
                JOIN categorylinks
                ON pg2.page_id = cl_from
                WHERE pg1.page_title = pg2.page_title
                AND pg2.page_namespace = 0
                AND cl_to = 'Living_people')
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg3
                JOIN categorylinks
                ON pg3.page_id = cl_from
                WHERE pg1.page_title = pg3.page_title
                AND pg3.page_namespace = 0
                AND cl_to = 'Possibly_living_people')
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg4
                JOIN categorylinks
                ON pg4.page_id = cl_from
                WHERE pg1.page_title = pg4.page_title
                AND pg4.page_namespace = 0
                AND cl_to = 'Human_name_disambiguation_pages')
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg5
                JOIN categorylinks
                ON pg5.page_id = cl_from
                WHERE pg1.page_title = pg5.page_title
                AND pg5.page_namespace = 0
                AND cl_to = 'Missing_people')
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg6
                JOIN categorylinks
                ON pg6.page_id = cl_from
                WHERE pg1.page_title = pg6.page_title
                AND pg6.page_namespace = 1
                AND cl_to = 'Musicians_work_group_articles')
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg7
                WHERE pg1.page_title = pg7.page_title
                AND pg7.page_namespace = 0
                AND pg7.page_is_redirect = 1)
AND EXISTS (SELECT
              1
            FROM page AS pg8
            JOIN templatelinks
            ON pg8.page_id = tl_from
            WHERE tl_namespace = 10
            AND tl_title = 'WPBiography'
            AND pg1.page_title = pg8.page_title
            AND pg8.page_namespace = 1)
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg9
                JOIN categorylinks
                ON pg9.page_id = cl_from
                WHERE pg1.page_title = pg9.page_title
                AND pg9.page_namespace = 0
                AND cl_to LIKE 'Musical_groups%')
AND NOT EXISTS (SELECT
                  1
                FROM page AS pg10
                JOIN categorylinks
                ON pg10.page_id = cl_from
                WHERE pg1.page_title = pg10.page_title
                AND pg10.page_namespace = 0
                AND cl_to LIKE '%music_groups')
LIMIT 2000;
''')

i = 1
output = []
for row in cursor.fetchall():
    if i > 1000:
        break
    page_title = re.sub('_', ' ', u'%s' % unicode(row[0], 'utf-8'))
    table_row = u'''| %d
| [[%s]]
|-''' % (i, page_title)
    if re.search(r'(^List of|^Line of|\bcontroversy\b|\belection\b|\bmurder(s)?\b|\binvestigation\b|\bkidnapping\b|\baffair\b|\ballegation\b|\brape(s)?\b| v. |\bfamily\b| and |\belection\b|\bband\b| of |\barchive\b|recordholders| & |^The|^[0-9]|\bfiction\b|\bcharacter\b| the |\bincident(s)?\b|\bprinciples\b|\bmost\b)', page_title, re.I):
        continue
    elif not re.search(r' ', page_title):
        continue
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
