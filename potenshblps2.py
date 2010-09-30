#!/usr/bin/env python2.5

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

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Potential biographies of living people (2)'

report_template = u'''
Articles that are in a "XXXX births" category (greater than 1899) that are \
not in [[:Category:Living people]], [[:Category:Possibly living people]], \
or a "XXXX deaths" category (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Biography
! Birth year
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* potenshblps2.py SLOW_OK */
SELECT
  page_title,
  cl_to
FROM page
JOIN categorylinks
ON cl_from = page_id
WHERE page_namespace = 0
AND page_is_redirect = 0
AND cl_to RLIKE '^[0-9]{4}_births$'
AND NOT EXISTS (SELECT
                  1
                FROM categorylinks
                WHERE cl_from = page_id
                AND cl_to LIKE '%_deaths')
AND NOT EXISTS (SELECT
                  1
                FROM categorylinks
                WHERE cl_from = page_id
                AND cl_to IN ('Living_people',
                              'Possibly_living_people',
                              'Disappeared_people',
                              'Missing_people',
                              'Year_of_death_unknown',
                              'Year_of_death_missing'))
ORDER BY cl_to DESC
LIMIT 1000;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[%s]]' % unicode(row[0], 'utf-8')
    birth_year = u'%s' % row[1].strip('_births')
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, birth_year)
    if int(birth_year) > 1899:
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
