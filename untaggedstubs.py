#!/usr/bin/env python
# Public domain; 2012; Legoktm
# Query written by Topbanana

import os
import datetime
import oursql
import wikitools
import settings

report_title = settings.rootpage + 'Untagged stubs'
report_template = u'''
Untagged stubs (limited to the first 800 results); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Title
! Length
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = oursql.connect(host=settings.host,
                      db=settings.dbname,
                      read_default_file=os.path.expanduser('~/.my.cnf'))
cursor = conn.cursor()
cursor.execute('''
/* shortnonstubs.py SLOW_OK */
SELECT
  page_title,
  page_len
FROM page
LEFT OUTER JOIN enwiki_p.categorylinks cc ON cl_from = page_id AND ( cl_to LIKE '%_stubs'
  OR cl_to IN ( 'All_disambiguation_pages', 'All_set_index_articles', 'Redirects_to_Wiktionary', 'Wikipedia_soft_redirects' ) )
WHERE page_namespace = 0
AND  page_title NOT LIKE 'List_of_%'
AND page_is_redirect = 0
AND cl_from IS NULL
AND  page_len < 1500
ORDER BY page_len ASC
LIMIT 800;
''')

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'%s' % unicode(row[0], 'utf-8')
    page_len = u'%s' % unicode(row[1], 'utf-8')
    table_row = u"""\
|-
| %d
| [[%s]]
| %s""" % (i, page_title, page_len)
    output.append(table_row)
    i+=1

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
