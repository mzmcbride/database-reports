#!/usr/bin/python

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

import codecs
import ConfigParser
import datetime
import MySQLdb, MySQLdb.cursors
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

skipped_pages = []
skipped_file = codecs.open('/home/mzmcbride/scripts/predadurr/skipped_pages.txt', 'r', 'utf-8')
for i in skipped_file.read().strip('\n').split('\n'):
    skipped_pages.append(i)
skipped_file.close()

excluded_titles = [
'^USS_',
'_[Ff]amily$',
'_[Mm]odel$',
'^FBI_',
'^The_',
'_School$',
'_Station$',
'_Band$',
'_Canada$',
'_Church$',
'_Tigers$',
'^List(s)?_of',
'^Numbers_in',
'^\d',
'\d$',
'_of_',
'_and_',
'_\&_',
'\(band\)',
'_FC$',
'_\([Ff]ilm\)$',
'_transmission$',
'_\(miniseries\)$',
'_College$',
'album\)$',
'song\)$',
'[Dd]isambiguation\)$',
'_Awards?$',
'_[Ss]chool',
'_team$',
'_[Hh]ighway',
]

excluded_templates = [
'infobox_single',
'infobox_book',
'infobox_television',
'infobox_stadium',
'infobox_company',
'infobox_motorsport_venue',
'infobox_album',
'infobox_tv_channel',
'infobox_film',
'infobox_television_film',
'infobox_software',
'infobox_television_season',
'infobox_scotus_case',
'infobox_golf_tournament',
'infobox_website',
'infobox_vg',
'infobox_university',
'infobox_podcast',
'infobox_bus_transit',
'infobox_shopping_mall',
'infobox_dotcom_company',
'infobox_painting',
'infobox_football_club',
's-rail-start',
]

excluded_titles_re = re.compile(r'(%s)' % '|'.join(str(i) for i in excluded_titles))
excluded_templates_re = re.compile(r'(%s)' % '|'.join(str(i) for i in excluded_templates), re.I|re.U)
capital_letters_re = re.compile(r'[A-Z]')

report_title = config.get('dbreps', 'rootpage') + 'Potential biographies of living people (5)'

report_template = u'''
Articles that potentially need to be in [[:Category:Living people]] (limited to the first 2000 \
entries). List generated mostly using magic; data as of <onlyinclude>%s</onlyinclude>.

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

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf', cursorclass=MySQLdb.cursors.SSCursor)
cursor = conn.cursor()
cursor.execute('SET SESSION group_concat_max_len = 1000000;')
cursor.execute('''
/* potenshblps5.py SLOW_OK */
SELECT
  page_title,
  GROUP_CONCAT(tl_title)
FROM page
LEFT JOIN templatelinks
ON tl_from = page_id
LEFT JOIN categorylinks
ON cl_from = page_id
WHERE page_namespace = 0
AND page_is_redirect = 0
AND cl_to IS NULL
GROUP BY page_id
ORDER BY page_id DESC
LIMIT 200000;
''')

i = 1
output = []
while True:
    row = cursor.fetchone()
    if i > 2000:
        break
    if row == None:
        break
    page_title = u'%s' % unicode(row[0], 'utf-8')
    if page_title in skipped_pages:
        continue
    if row[1] is not None:
        tl_title = u'%s' % unicode(row[1], 'utf-8')
    else:
        tl_title = ''
    if (
        not excluded_titles_re.search(page_title) and
        page_title.find('_') != -1 and
        len(capital_letters_re.findall(page_title)) > 1 and
        not excluded_templates_re.search(tl_title)
        ):
        table_row = u'''| %d
| [[%s]]
|-''' % (i, page_title)
        output.append(table_row)
        i += 1

cursor.close()

cursor = conn.cursor()
cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
