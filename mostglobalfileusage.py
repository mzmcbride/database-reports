#! /usr/bin/env python
# Public domain; MZMcBride; 2011

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Files with the most uses globally'

report_template = u'''\
Files with the most uses globally; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! File
! Uses
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* mostglobalfileusage.py SLOW_OK */
SELECT
  gil_to,
  COUNT(*)
FROM globalimagelinks
GROUP BY gil_to
ORDER BY COUNT(*) DESC, gil_to ASC
LIMIT 1000;
''')

i = 1
output = []
for row in cursor.fetchall():
    gil_to = u'[[:File:%s|%s]]' % (unicode(row[0], 'utf-8'), unicode(row[0], 'utf-8'))
    count = row[1]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, gil_to, count)
    output.append(table_row)
    i += 1

cursor.execute('''
               SELECT
                 UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp)
               FROM recentchanges
               ORDER BY rc_timestamp DESC
               LIMIT 1;
               ''')
rep_lag = cursor.fetchone()[0]
time_diff = datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)
current_of = time_diff.strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
