#! /usr/bin/env python
# Public domain; bjweeks, MZMcBride; 2012

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Potential biographies of living people (2)'

report_template = u'''\
Articles that are in a "XXXX births" category (greater than 1899) that are \
not in [[:Category:Living people]], [[:Category:Possibly living people]], \
or a "XXXX deaths" category (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Biography
! Birth year
|-
%s
|}
'''

excluded_categories = ['Living_people',
                       'Possibly_living_people',
                       'Disappeared_people',
                       'Missing_people',
                       'Year_of_death_unknown',
                       'Year_of_death_missing',
                       '20th-century_deaths',
                       '21st-century_deaths',
                       '1900s_deaths',
                       '2000s_deaths']

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host,
                       db=settings.dbname,
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()

skip_page_ids = set()

for cat in excluded_categories:
    cursor.execute('''
    /* potenshblps2.py SLOW_OK */
    SELECT
      cl_from
    FROM categorylinks
    WHERE cl_to = %s;
    ''' , cat)
    results = cursor.fetchall()
    for row in results:
        cl_from = row[0]
        skip_page_ids.add(cl_from)

for year in range(1900, int(datetime.datetime.utcnow().strftime('%Y'))+1):
    cursor.execute('''
    /* potenshblps2.py SLOW_OK */
    SELECT
      cl_from
    FROM categorylinks
    WHERE cl_to = '%s_deaths';
    ''' % year)
    results = cursor.fetchall()
    for row in results:
        cl_from = row[0]
        skip_page_ids.add(cl_from)

for year in range(1900, int(datetime.datetime.utcnow().strftime('%Y'))+1, 10):
    cursor.execute('''
    /* potenshblps2.py SLOW_OK */
    SELECT
      cl_from
    FROM categorylinks
    WHERE cl_to = '%ss_deaths';
    ''' % year)
    results = cursor.fetchall()
    for row in results:
        cl_from = row[0]
        skip_page_ids.add(cl_from)

target_page_ids = []
for year in range(1900, int(datetime.datetime.utcnow().strftime('%Y'))+1):
    cursor.execute('''
    /* potenshblps2.py SLOW_OK */
    SELECT
      cl_from
    FROM categorylinks
    WHERE cl_to = '%s_births';
    ''' % year)
    results = cursor.fetchall()
    for result in results:
        cl_from = result[0]
        if cl_from not in skip_page_ids:
            target_page_ids.append(str(cl_from))

cursor.execute('''
/* potenshblps2.py SLOW_OK */
SELECT
  page_title,
  cl_to
FROM page
JOIN categorylinks
ON cl_from = page_id
WHERE page_id IN (%s)
AND cl_to LIKE '%%_births'
AND page_namespace = 0
AND page_is_redirect = 0
ORDER BY cl_to DESC;
''' % (','.join(target_page_ids)))

i = 1
output = []
for row in cursor.fetchall():
    page_title = u'[[%s]]' % unicode(row[0], 'utf-8')
    birth_year = u'%s' % row[1].strip('_births')
    table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, birth_year)
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
