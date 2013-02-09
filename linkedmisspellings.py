#! /usr/bin/env python
# Public domain; MZMcBride; 2012

import ConfigParser
import datetime
import MySQLdb
import os
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Linked misspellings'
report_template = u'''\
Linked misspellings (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Incoming links
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file=os.path.expanduser('~/.my.cnf'))
cursor = conn.cursor()
cursor.execute('''
/* linkedmisspellings.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN categorylinks
ON page_id = cl_from
WHERE page_namespace = 0
AND page_is_redirect = 1
AND cl_to = 'Redirects_from_misspellings';
''')

misspelled_redirects = set()

for row in cursor.fetchall():
    misspelled_redirects.add(row[0])

def count_incoming_links(cursor, page_title):
    cursor.execute('''
    /* linkedmisspellings.py SLOW_OK */
    SELECT
      COUNT(*)
    FROM pagelinks
    JOIN page
    ON pl_from = page_id
    WHERE pl_namespace = 0
    AND pl_title = %s
    AND page_namespace = 0;
    ''' , page_title)
    result = cursor.fetchone()
    if result:
        count = int(result[0])
    else:
        count = 0
    return count

i = 1
output = []
for misspelled_redirect in misspelled_redirects:
    if i > 1000:
        break
    incoming_links = count_incoming_links(cursor, misspelled_redirect)
    if incoming_links:
        table_row = u"""\
|-
| %d
| {{dbr link|1=%s}}
| %d""" % (i, misspelled_redirect.decode('utf-8'), incoming_links)
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
