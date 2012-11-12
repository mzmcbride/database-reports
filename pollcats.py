#! /usr/bin/env python
# Public domain; bjweeks, MZMcBride, CBM; 2012

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Polluted categories'

report_template = u'''\
Categories that contain pages in the (Main) namespace and the user namespaces \
(limited to the first 1000 entries); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host,
                       db=settings.dbname,
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()

# Establish a few lists.
all_category_titles = []
polluted_category_titles = []

# Grab a list of all pages in the Category namespace.
cursor.execute('''
/* pollcats.py SLOW_OK */
SELECT
  page_title
FROM page
WHERE page_namespace = 14;
''')

for row in cursor.fetchall():
    # FIXME: Don't stick all these in memory.
    all_category_titles.append(row[0])

# Find all the categories that are specifically marked as polluted.
cursor.execute('''
/* pollcats.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN templatelinks
ON tl_from = page_id
WHERE page_namespace = 14
AND tl_namespace = 10
AND tl_title = 'Polluted_category';
''')

for row in cursor.fetchall():
    polluted_category_titles.append(row[0])

i = 1
output = []
for title in all_category_titles:
    if i > 1000:
        break
    elif title in polluted_category_titles:
        continue
    else:
        cursor.execute('''
        /* pollcats.py SLOW_OK */
        SELECT
          1
        FROM page
        JOIN categorylinks
        ON cl_from = page_id
        WHERE cl_to = %s
        AND page_namespace IN (2,3)
        LIMIT 1;
        ''' , title)
        user_result = cursor.fetchone()
        if user_result:
            cursor.execute('''
            /* pollcats.py SLOW_OK */
            SELECT
              1
            FROM page
            JOIN categorylinks
            ON cl_from = page_id
            WHERE cl_to = %s
            AND page_namespace = 0
            LIMIT 1;
            ''' , title)
            main_result = cursor.fetchone()
            if main_result:
                cl_to = u'{{dbr link|1=%s}}' % unicode(title, 'utf-8')
                table_row = u'''\
| %d
| %s
|-''' % (i, cl_to)
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
