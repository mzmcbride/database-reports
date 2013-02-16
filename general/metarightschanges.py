#!/usr/bin/python

# Copyright 2011 bjweeks, MZMcBride

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

report_title = config.get('dbreps', 'rootpage') + 'Meta-Wiki rights changes'

report_template = u'''
Rights changes at Meta-Wiki that applied to local accounts; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! User
! Actor
! Timestamp
! Previous rights
! Subsequent rights
! Comment
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host='metawiki-p.rrdb.toolserver.org',
                       db='metawiki_p',
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* metarightschanges.py SLOW_OK */
SELECT
  log_title,
  user_name,
  log_timestamp,
  log_params,
  log_comment
FROM logging_ts_alternative
JOIN user
ON log_user = user_id
WHERE log_namespace = 2
AND log_title LIKE %s
AND log_type = 'rights'
ORDER BY log_timestamp DESC;
''' , '%@'+config.get('dbreps', 'dbname').strip('_p'))

i = 1
output = []
for row in cursor.fetchall():
    log_title = unicode(row[0], 'utf-8')
    user_name = unicode(row[1], 'utf-8')
    log_timestamp = row[2]
    log_params = row[3]
    try:
        previous_rights = log_params.split('\n', 1)[0]
        subsequent_rights = log_params.split('\n', 1)[1]
    except IndexError:
        previous_rights = ''
        subsequent_rights = ''
    log_comment = '<div style="width:350px; word-wrap:break-word;"><nowiki>'+unicode(row[4], 'utf-8')+'</nowiki></div>'
    table_row = u'''| %d
| %s
| %s
| %s
| %s
| %s
| %s
|-''' % (i, log_title, user_name, log_timestamp, previous_rights, subsequent_rights, log_comment)
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
