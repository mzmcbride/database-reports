#!/usr/bin/python
# Public domain; MZMcBride; 2012

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Articles containing overlapping coordinates'

report_template = u'''
Articles that contain {{tl|Coord/display/inline,title}} and \
{{tl|Coord/display/title}}; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
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

inline_title_pages = set()
cursor.execute('''
/* coordoverlap.py SLOW_OK */
SELECT
  page_id
FROM page
JOIN templatelinks
ON tl_from = page_id
WHERE page_namespace = 0
AND tl_namespace = 10
AND tl_title = 'Coord/display/inline,title';
''')

for row in cursor.fetchall():
    inline_title_pages.add(row[0])

title_pages = set()
cursor.execute('''
/* coordoverlap.py SLOW_OK */
SELECT
  page_id
FROM page
JOIN templatelinks
ON tl_from = page_id
WHERE page_namespace = 0
AND tl_namespace = 10
AND tl_title = 'Coord/display/title';
''')

for row in cursor.fetchall():
    title_pages.add(row[0])

i = 1
output = []
for page_id in inline_title_pages:
    if page_id in title_pages:
        cursor.execute('''
        /* coordoverlap.py SLOW_OK */
        SELECT
          page_title
        FROM page
        WHERE page_id = %s;
        ''' , int(page_id))
        page_title = u'[[%s]]' % unicode(cursor.fetchone()[0], 'utf-8')
        table_row = u'''\
| %d
| %s
|-''' % (i, page_title)
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
