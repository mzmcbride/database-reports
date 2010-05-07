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
import re
import wikitools
import settings

report_title = settings.rootpage + 'Non-free files missing a rationale'

report_template = u'''
Non-free files missing a [[WP:FUR|fair use rationale]] (limited results); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! File
|-
%s
|}
'''

fair_use_strings = [
r'=.*(fair[ -]?use|non[ -]?free|rationale).*=',
r'rationale for the fair use',
r'qualifies as fair use',
r'fair use in \[\[',
r'\'\'\'fair use rationale[:]?\'\'\'',
r'the doctrine of fair use',
r'the purpose of this image',
r'this low quality image',
r'use of this image will not decrease',
r'conforms with the requirements',
r'is a low resolution screenshot'
r'is a low resolution of the original',
r'used here for purely encyclopedic and informational purposes',
r'use of this low-resolution version',
r'does not in any way limit the ability of the copyright',
r'rationale for use on',
r'image is suitable for fair use on',
r'is a low resolution copy of the original',
r'rationale:',
r'is only being used for informational purposes',	
r'constitutes fair use',
r'does not deprive the owner of any revenue',
r'no free substitute can be made',
r'does not limit the copyright owner\'s rights',
r'within fair use guidelines',
r'fair use rationale:',
r'qualifies for fair use',
r'is a low-resolution image',
r'image is being used to illustrate',
r'Fair Use Rationale for',
r'for the purposes of criticism and comment',
r'contributes to the article significantly',
r'does not limit the copyright owner\'s ability',
r'no free equivalent is available',
r'does not limit the copyright holder\'s ability',
r'enhances the article in which it\'s displayed',
r'falls under fair use as',
r'will not limit the .+ ability',
r'a historically significant photo',
r'much lower resolution than the original',
r'image is of low size and quality',
r'used under a claim of fair use',
r'used for the educational purposes',
r'only for educational purposes and is not used for profit',
r'depicts a.+historic event',
r'quality of the image is very low',
r'Purpose is purely informational',
r'considerably lower resolution than the original',
]

find_fair_use_strings = re.compile(r"(%s)" % '|'.join(str(i) for i in fair_use_strings), re.I)

wiki = wikitools.Wiki(settings.apiurl); wiki.setMaxlag(-1)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* nonfreemissingrat.py SLOW_OK */
SELECT DISTINCT
  pg1.page_id,
  pg1.page_title
FROM page AS pg1
JOIN templatelinks
ON pg1.page_id = tl_from
WHERE tl_namespace = 10
AND tl_title IN (SELECT
                   page_title
                 FROM page
                 JOIN categorylinks
                 ON cl_from = page_id
                 WHERE page_namespace = 10
                 AND cl_to = 'Non-free_Wikipedia_file_copyright_tags')
AND NOT EXISTS (SELECT
                  1
                FROM templatelinks
                WHERE tl_from = pg1.page_id
                AND tl_title IN (SELECT
                                   page_title
                                 FROM page
                                 JOIN categorylinks
                                 ON cl_from = page_id
                                 WHERE page_namespace = 10
                                 AND cl_to = 'Non-free_use_rationale_templates'))
AND pg1.page_namespace = 6
LIMIT 20000;
''')

f = open('%snonfree-reviewed-page-ids.txt' % settings.path, 'r')
reviewed_page_ids = f.read()
reviewed_page_ids_list = reviewed_page_ids.split('\n')
f.close()

i = 1
output = []
g = open('%snonfree-reviewed-page-ids.txt' % settings.path, 'a')
for row in cursor.fetchall():
    page_id = row[0]
    page_title = u'%s' % unicode(row[1], 'utf-8')
    if str(page_id) in reviewed_page_ids_list:
        continue
    page = wikitools.Page(wiki, 'File:%s' % page_title, followRedir=False)
    table_row = u'''| %d
| [[:File:%s|%s]]
|-''' % (i, page_title, page_title)
    try:
        page_text = page.getWikiText()
    except:
        pass
    if page.exists and not find_fair_use_strings.search(page_text):
        output.append(table_row)
        i += 1
    else:
        g.write('%s\n' % page_id)
g.close()

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=settings.editsumm, bot=1)

cursor.close()
conn.close()
