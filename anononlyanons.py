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

report_title = config.get('dbreps', 'rootpage') + 'Short user talk pages for IPs'

report_template = u'''\
User talk pages of anonymous users where the only contributors to the page \
are anonymous, the page is less than 50 bytes in length, and it contains no \
templates (limited to the first 1000 entries); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Length
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

pages = set()
cursor.execute('''
/* anononlyanons.py SLOW_OK */
SELECT
  page_id,
  page_title
FROM page
WHERE page_namespace = 3
AND page_len < 50;
''')
results = cursor.fetchall()
for result in results:
    page_id = result[0]
    page_title = result[1]
    if re.search(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', page_title):
        pages.add(page_id)

target_page_ids = []
for page in pages:
    cursor.execute('''
    /* anononlyanons.py SLOW_OK */
    SELECT
      COUNT(*)
    FROM revision
    WHERE rev_page = %s
    AND rev_user != 0;
    ''' , page)
    registered_user_contribs_count = cursor.fetchone()
    if registered_user_contribs_count:
        if int(registered_user_contribs_count[0]) == 0:
            cursor.execute('''
            /* anononlyanons.py SLOW_OK */
            SELECT
              COUNT(*)
            FROM templatelinks
            WHERE tl_from = %s;
            ''' , page)
            template_count = cursor.fetchone()
            if template_count:
                if int(template_count[0]) == 0:
                    target_page_ids.append(str(page))

cursor.execute('''
/* anononlyanons.py SLOW_OK */
SELECT DISTINCT
  ns_name,
  page_title,
  page_len
FROM page
JOIN toolserver.namespace
ON dbname = '%s'
AND page_namespace = ns_id
WHERE page_id IN (%s);
''' % (config.get('dbreps', 'dbname'), ', '.join(target_page_ids)))

i = 1
output = []
for row in cursor.fetchall():
    ns_name = u'%s' % unicode(row[0], 'utf-8')
    page_title = u'%s' % unicode(row[1], 'utf-8')
    full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
    page_len = row[2]
    table_row = u'''| %d
| %s
| %s
|-''' % (i, full_page_title, page_len)
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
