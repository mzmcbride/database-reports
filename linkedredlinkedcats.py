#! /usr/bin/env python
# Public domain; MZMcBride; 2012

import ConfigParser
import datetime
import MySQLdb
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Red-linked categories with incoming links'

report_template = u'''\
Red-linked categories with incoming links; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
! Links
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

categories = set()
cursor.execute('''
/* linkedredlinkedcats.py SLOW_OK */
SELECT
  cl_to
FROM categorylinks
LEFT JOIN page
ON cl_to = page_title
AND page_namespace = 14
WHERE page_title IS NULL;
''')
results = cursor.fetchall()
for result in results:
    cl_to = result[0]
    categories.add(cl_to)

def get_significant_incoming_links_count(cursor, category_name):
    cursor.execute('''
    SELECT
      COUNT(*)
    FROM page
    JOIN pagelinks
    ON pl_from = page_id
    WHERE pl_namespace = 14
    AND pl_title = %s
    AND page_namespace IN (0,6,10,12,14,100);
    ''' , category_name)
    data = cursor.fetchone()
    if data:
        if int(data[0]) > 0:
            return data[0]
    return False

i = 1
output = []
for category in categories:
    if i > 1000:
        break
    links = get_significant_incoming_links_count(cursor, category)
    if links:
        category_link = u'[[Special:WhatLinksHere/Category:%s|%s]]' % (unicode(category, 'utf-8'),
                                                                       unicode(category, 'utf-8'))
        table_row = u'''\
| %d
| %s
| %s
|-''' % (i, category_link, links)
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
