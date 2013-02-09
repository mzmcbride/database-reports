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
import math
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Potential reviewer candidates/%i'

report_template = u'''
Users with more than 2,500 edits, their first edit more than a year ago, \
and their latest edit within the past month; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! Edit count
! First edit
! Latest edit
! Groups
|-
%s
|}
'''

rows_per_page = 2000

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()

exceptions = []
cursor.execute('''
/* reviewercandidates.py SLOW_OK */
SELECT DISTINCT
  pl_title
FROM pagelinks
JOIN page
ON pl_from = page_id
WHERE page_namespace = 4
AND page_title = 'Database_reports/Potential_reviewer_candidates/Exceptions'
AND pl_namespace IN (2,3)
AND pl_title NOT LIKE '%/%';
''')
for row in cursor.fetchall():
    exception = u'%s' % unicode(row[0].replace('_', ' '), 'utf-8')
    exceptions.append(exception)

cursor.execute('''
/* reviewercandidates.py SLOW_OK */
SELECT DISTINCT
  usrtmp.user_name,
  usrtmp.user_editcount,
  usrtmp.rev_timestamp AS first_edit,
  rv1.rev_timestamp AS last_edit,
  usrtmp.groups
FROM revision AS rv1
JOIN (SELECT
        user_id,
        user_name,
        user_editcount,
        rev_timestamp,
        GROUP_CONCAT(ug_group) AS groups
      FROM user
      LEFT JOIN user_groups
      ON ug_user = user_id
      JOIN revision
      ON rev_user = user_id
      WHERE user_editcount > 2500
      AND user_id NOT IN (SELECT
                            ug_user
                          FROM user_groups
                          WHERE ug_group IN ("bot", "sysop", "reviewer"))
      AND rev_timestamp = (SELECT
                             MIN(rev_timestamp)
                           FROM revision
                           WHERE rev_user = user_id)
      AND rev_timestamp < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 1 YEAR),'%Y%m%d%H%i%s')
      GROUP BY user_id) AS usrtmp
ON usrtmp.user_id = rv1.rev_user
WHERE rv1.rev_timestamp = (SELECT
                             MAX(rev_timestamp)
                           FROM revision
                           WHERE rev_user = usrtmp.user_id)
AND rv1.rev_timestamp > DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 1 MONTH),'%Y%m%d%H%i%s')
ORDER BY usrtmp.user_name ASC;
''')

i = 1
output = []
for row in cursor.fetchall():
    user_name = u'%s' % unicode(row[0], 'utf-8')
    if user_name in exceptions:
        continue
    user_editcount = row[1]
    first_edit = row[2]
    last_edit = row[3]
    groups = row[4]
    if groups:
        groups = u'%s' % unicode(groups.replace(',', ', '), 'utf-8')
    else:
        groups = ''
    table_row = u'''|%d
|[[User:%s|%s]]
|%s
|%s
|%s
|%s
|-''' % (i, user_name, user_name, user_editcount, first_edit, last_edit, groups)
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
