#!/usr/bin/python

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

import ConfigParser
import datetime
import math
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Deleted red-linked categories/%i'

report_template = u'''
Deleted red-linked categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
! Members (stored)
! Members (dynamic)
! Admin
! Timestamp
! Comment
%s
|}
'''

rows_per_page = 500

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl')); wiki.setMaxlag(-1)
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

def get_last_log_entry(cursor, cl_to):
    cursor.execute('''
    /* deletedredlinkedcats.py SLOW_OK */
    SELECT
      log_timestamp,
      user_name,
      log_comment
    FROM logging_ts_alternative
    JOIN user
    ON log_user = user_id
    WHERE log_type = 'delete'
    AND log_action = 'delete'
    AND log_namespace = 14
    AND log_title = %s
    ORDER BY log_timestamp DESC
    LIMIT 1;
    ''' , cl_to)
    for row in cursor.fetchall():
        log_timestamp = row[0]
        user_name = unicode(row[1], 'utf-8')
        log_comment = unicode(row[2], 'utf-8')
    return { 'timestamp': log_timestamp, 'user': user_name, 'comment': log_comment }

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* deletedredlinkedcats.py SLOW_OK */
SELECT DISTINCT
  ns_name,
  cl_to,
  cat_pages
FROM categorylinks
JOIN category
ON cl_to = cat_title
JOIN toolserver.namespace
ON dbname = %s
AND ns_id = 14
LEFT JOIN page
ON cl_to = page_title
AND page_namespace = 14
WHERE page_title IS NULL
AND cat_pages > 0;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    ns_name = row[0]
    cl_to = row[1]
    try:
        log_props = get_last_log_entry(cursor, cl_to)
        user_name = log_props['user']
        log_timestamp = log_props['timestamp']
        log_comment = log_props['comment']
        if log_comment:
            log_comment = u'<nowiki>%s</nowiki>' % log_comment
    except:
        user_name = None
        log_timestamp = None
        log_comment = None
    if not user_name or not log_timestamp:
        continue
    dynamic_count = u'{{PAGESINCATEGORY:%s}}' % unicode(cl_to, 'utf-8')
    cl_to = u'[[:%s:%s|%s]]' % (unicode(ns_name, 'utf-8'), unicode(cl_to, 'utf-8'), unicode(cl_to,'utf-8'))
    stored_count = row[2]
    table_row = u'''|-
| %d
| %s
| %s
| %s
| %s
| %s
| %s''' % (i, cl_to, stored_count, dynamic_count, user_name, log_timestamp, log_comment)
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
