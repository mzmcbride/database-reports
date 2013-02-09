#!/usr/bin/env python2.5

# Copyright 2010 bjweeks, Multichil, MZMcBride

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
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Articles containing deleted files/%i'

report_template = u'''
Articles containing a deleted file; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! File
! Timestamp
! Comment
%s
|}
'''

rows_per_page = 1000

def get_deleted_props(cursor, il_to):
    cursor.execute('''
    /* deletedfilesinarticles.py SLOW_OK */
    SELECT
      log_timestamp,
      log_comment
    FROM logging_ts_alternative
    WHERE log_type = 'delete'
    AND log_action = 'delete'
    AND log_namespace = 6
    AND log_title = %s
    ORDER BY log_timestamp DESC
    LIMIT 1;
    ''' , il_to)
    results = cursor.fetchone()
    if results:
        return results
    return False

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* deletedfilesinarticles.py SLOW_OK */
SELECT
  page_title,
  il_to
FROM page
JOIN imagelinks
ON page_id = il_from
WHERE (NOT EXISTS (SELECT
                     1
                   FROM image
                   WHERE img_name = il_to))
AND (NOT EXISTS (SELECT
                   1
                 FROM commonswiki_p.page
                 WHERE page_title = CAST(il_to AS CHAR)
                 AND page_namespace = 6))
AND (NOT EXISTS (SELECT
                   1
                 FROM page
                 WHERE page_title = il_to
                 AND page_namespace = 6))
AND page_namespace = 0;
''')

i = 1
output = []
for row in cursor.fetchall():
    il_to = row[1]
    deleted_props = get_deleted_props(cursor, il_to)
    if not deleted_props:
        continue
    page_title = u'[[%s]]' % unicode(row[0], 'utf-8')
    il_to = u'[[:File:%s|%s]]' % (unicode(il_to, 'utf-8'), unicode(il_to, 'utf-8'))
    log_timestamp = deleted_props[0]
    log_comment = unicode('<nowiki>'+deleted_props[1]+'</nowiki>', 'utf-8')
    table_row = u'''|-
| %d
| %s
| %s
| %s
| %s''' % (i, page_title, il_to, log_timestamp, log_comment)
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
    report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)
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
