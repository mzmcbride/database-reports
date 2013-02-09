#! /usr/bin/env python
# Public domain; Topbanana, Legoktm, MZMcBride; 2012

import ConfigParser
import datetime
import os
import os
import oursql
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Untagged stubs'
report_template = u'''\
Untagged stubs (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Title
! Length
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = oursql.connect(host=config.get('dbreps', 'host'),
                      db=config.get('dbreps', 'dbname'),
                      read_default_file=os.path.expanduser('~/.my.cnf'))
cursor = conn.cursor()
cursor.execute('''
/* untaggedstubs.py SLOW_OK */
SELECT
  page_id,
  page_title,
  page_len
FROM page
LEFT JOIN categorylinks
ON cl_from = page_id
AND cl_to LIKE '%_stubs'
WHERE page_namespace = 0
AND page_is_redirect = 0
AND cl_from IS NULL
AND page_len < 1500;
''')

non_stubs = cursor.fetchall()

cursor.execute('''
/* untaggedstubs.py SLOW_OK */
SELECT
  page_id
FROM page
JOIN categorylinks
ON cl_from = page_id
WHERE page_namespace = 0
AND cl_to IN ('All_disambiguation_pages',
              'All_set_index_articles',
              'Redirects_to_Wiktionary',
              'Wikipedia_soft_redirects');
''')

known_shorties = []
for row in cursor.fetchall():
    page_id = int(row[0])
    known_shorties.append(page_id)

i = 1
output = []
for row in non_stubs:
    if i > 1000:
        break
    page_id = int(row[0])
    page_title = u'%s' % unicode(row[1], 'utf-8')
    page_len = row[2]
    if (page_title.startswith('List_of_') or
        page_id in known_shorties):
        continue
    table_row = u"""\
|-
| %d
| [[%s]]
| %s""" % (i, page_title, page_len)
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
