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
import MySQLdb
import wikitools
import settings

report_title = 'Wikipedia:Database reports/Mistagged non-free content'

report_template = u'''
Mistagged non-free content; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Local file
! Commons file
|-
%s
|}
'''

wiki = wikitools.Wiki()
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host='sql-s1', db='enwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* mistaggedfiles.py SLOW_OK */
SELECT
  DISTINCT(enwiki_p.page.page_title),
  commonswiki_p.image.img_name
FROM enwiki_p.image, commonswiki_p.image, enwiki_p.categorylinks, enwiki_p.page
WHERE enwiki_p.image.img_sha1 = commonswiki_p.image.img_sha1
AND enwiki_p.page.page_title = enwiki_p.image.img_name
AND enwiki_p.categorylinks.cl_from = enwiki_p.page.page_id
AND enwiki_p.categorylinks.cl_to = 'All_non-free_media'
AND enwiki_p.image.img_sha1 != 'phoiac9h4m842xq45sp7s6u21eteeq1';
''')

i = 1
output = []
for row in cursor.fetchall():
    en_file = u'[[:File:%s|%s]]' % (unicode(row[0], 'utf-8'), unicode(row[0], 'utf-8'))
    commons_file = u'[[:commons:File:%s|%s]]' % (unicode(row[1], 'utf-8'), unicode(row[1], 'utf-8'))
    table_row = u'''| %d
| %s
| %s
|-''' % (i, en_file, commons_file)
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