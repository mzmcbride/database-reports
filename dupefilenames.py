#! /usr/bin/env python
# Public domain; MZMcBride; 2011

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Largely duplicative file names'

report_template = u'''\
Largely duplicative file names (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:80%%;"
|- style="white-space:nowrap;"
! No.
! Normalized name
! Count
! Real names
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host,
                       db=settings.dbname,
                       read_default_file='~/.my.cnf',
                       charset='utf8')

output = []
i = 1
cursor = conn.cursor()
cursor.execute('''
/* dupefilenames.py SLOW_OK */
SELECT
  LOWER(CONVERT(page_title USING utf8)),
  GROUP_CONCAT(page_title SEPARATOR '|'),
  COUNT(*)
FROM page
WHERE page_namespace = 6
GROUP BY 1
HAVING COUNT(*) > 1
LIMIT 1000;
''')
for row in cursor.fetchall():
    norm_name = row[0]
    orig_names = []
    for name in row[1].split('|'):
        name = u'[[:File:%s|%s]]' % (unicode(name, 'utf-8'), unicode(name, 'utf-8'))
        orig_names.append(name)
    orig_name = ', '.join(orig_names)
    count = row[2]
    table_row = u'''\
| %d
| %s
| %s
| %s
|-''' % (i, norm_name, count, orig_name)
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
report.edit(report_text, summary=settings.editsumm, bot=1)

cursor.close()
conn.close()
