#!/usr/bin/python
# Public domain; bjweeks, MZMcBride; 2012

import ConfigParser
import datetime
import MySQLdb
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Orphaned talk pages'

report_template = u'''\
Orphaned talk pages. Pages transcluding {{[[Template:Go away|Go away]]}} or \
{{[[Template:G8-exempt|G8-exempt]]}} have been excluded. Data as of \
<onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

def check_commons(commons_cursor, file_name):
    commons_cursor.execute('''
    /* orphanedtalks.py */
    SELECT
      1
    FROM page
    WHERE page_namespace = 6
    AND page_title = %s;
    ''' , file_name)
    result = commons_cursor.fetchone()
    if result:
        if int(result[0]) == 1:
            return True
    return False

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* orphanedtalks.py SLOW_OK */
SELECT
  p1.page_id,
  p1.page_namespace,
  ns_name,
  p1.page_title
FROM page AS p1
LEFT JOIN page AS p2
ON p2.page_title = p1.page_title
AND p2.page_namespace = p1.page_namespace-1
JOIN toolserver.namespace
ON p1.page_namespace = ns_id
AND dbname = %s
WHERE p1.page_title NOT LIKE '%%/%%'
AND p1.page_namespace mod 2 != 0
AND p1.page_namespace NOT IN (3,9)
AND p2.page_id IS NULL;
''' , config.get('dbreps', 'dbname'))

results = cursor.fetchall()

excluded_page_ids = set()
cursor.execute('''
/* orphanedtalks.py SLOW_OK */
SELECT
  page_id
FROM page
JOIN templatelinks
ON page_id = tl_from
WHERE tl_title IN ('G8-exempt', 'Go_away', 'Rtd')
AND tl_namespace = 10;
''')
for row in cursor.fetchall():
    page_id = row[0]
    excluded_page_ids.add(page_id)

commons_conn = MySQLdb.connect(host='sql-s4',
                               db='commonswiki_p',
                               read_default_file='~/.my.cnf')
commons_cursor = commons_conn.cursor()

i = 1
output = []
for row in results:
    page_id = row[0]
    if page_id in excluded_page_ids:
        continue
    page_namespace = row[1]
    if page_namespace == 7:
        if check_commons(commons_cursor, row[3]):
            continue

    ns_name = u'%s' % unicode(row[2], 'utf-8')
    page_title = u'%s' % unicode(row[3], 'utf-8')
    if page_namespace == 6 or page_namespace == 14:
        page_title = ':%s:%s' % (ns_name, page_title)
    elif ns_name:
        page_title = '%s:%s' % (ns_name, page_title)
    else:
        page_title = '%s' % (page_title)

    search_strings = ['archive',
                      '^Image:',
                      '^Image_talk:',
                      '^File:',
                      '^File_talk:',
                      '^Category:',
                      '^User:',
                      '^User_talk:',
                      '^Template:',
                      '^Talk:Talk:']
    if (re.search(r'\\', row[3], re.I|re.U) or
        re.search(r'(%s)' % '|'.join(search_strings), row[3], re.I|re.U)):
        continue

    table_row = u'''\
|-
| %d
| {{plnr|1=%s}}''' % (i, page_title)
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

commons_cursor.close()
commons_conn.close()

cursor.close()
conn.close()
