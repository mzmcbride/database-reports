#! /usr/bin/env python
# Public domain; bjweeks, MZMcBride; 2011

import ConfigParser
import datetime
import math
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Unused templates/%i'

report_template = u'''\
Unused templates; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Template
|-
%s
|}
'''

rows_per_page = 1000

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

def get_substituted_templates(cursor):
    templates = []
    cursor.execute('''
    /* unusedtemplates.py */
    SELECT
      page_title
    FROM page
    JOIN categorylinks
    ON page_id = cl_from
    WHERE cl_to = 'Wikipedia_substituted_templates'
    AND page_namespace = 10;
    ''')
    for row in cursor.fetchall():
        page_title = unicode(row[0], 'utf-8')
        templates.append(page_title)
    return templates

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()
substituted_templates = get_substituted_templates(cursor)

cursor.execute('''
/* unusedtemplates.py SLOW_OK */
SELECT
  ns_name,
  page_title
FROM page
JOIN toolserver.namespace
ON dbname = %s
AND page_namespace = ns_id
LEFT JOIN redirect
ON rd_from = page_id
LEFT JOIN templatelinks
ON page_namespace = tl_namespace
AND page_title = tl_title
WHERE page_namespace = 10
AND rd_from IS NULL
AND tl_from IS NULL;
''' , config.get('dbreps', 'dbname'))

i = 1
output = []
for row in cursor.fetchall():
    ns_name = u'%s' % unicode(row[0], 'utf-8')
    page_title = u'%s' % unicode(row[1], 'utf-8')
    full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
    table_row = u'''\
| %d
| %s
|-''' % (i, full_page_title)
    if (not page_title.endswith('/doc') and
        not page_title.endswith('/testcases') and
        not page_title.endswith('/sandbox') and
        not page_title.startswith('Editnotices/') and
        not page_title.startswith('Cite_doi/') and
        not page_title.startswith('Cite_pmid/') and
        not page_title.startswith('TFA_title/') and
        not page_title.startswith('POTD_protected/') and
        not page_title.startswith('POTD_credit/') and
        not page_title.startswith('POTD_caption/') and
        not page_title.startswith('Did_you_know_nominations/') and
        not page_title.startswith('Child_taxa//') and
        page_title not in substituted_templates):
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

end = rows_per_page
page = 1
for start in range(0, len(output), rows_per_page):
    report = wikitools.Page(wiki, report_title % page)
    report_text = report_template % (current_of, '\n'.join(output[start:end]))
    report_text = report_text.encode('utf-8')
    report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)
    page += 1
    end += rows_per_page

page = math.ceil(len(output) / float(rows_per_page)) + 1
while 1:
    report = wikitools.Page(wiki, report_title % page)
    report_text = config.get('dbreps', 'blankcontent')
    report_text = report_text.encode('utf-8')
    if not report.exists:
        break
    report.edit(report_text, summary=config.get('dbreps', 'blanksumm'), bot=1)
    page += 1

cursor.close()
conn.close()
