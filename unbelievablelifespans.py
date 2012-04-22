#! /usr/bin/env python
# Public domain; MZMcBride; 2012

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Unbelievable life spans'

report_template = u'''\
Unbelievable life spans; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Page
! Birth year
! Death year
! Life span
|-
%s
|}
'''

current_year = int(datetime.datetime.utcnow().strftime('%Y'))

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

conn = MySQLdb.connect(host=settings.host,
                       db=settings.dbname,
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()

birth_years = {}
death_years = {}

for year in range(1, current_year+1):
    cursor.execute('''
    /* unbelievablelifespans.py SLOW_OK */
    SELECT
      cl_from
    FROM categorylinks
    WHERE cl_to = '%s_births';
    ''' % year)
    results = cursor.fetchall()
    for result in results:
        cl_from = int(result[0])
        birth_years[cl_from] = year

for year in range(1, current_year+1):
    cursor.execute('''
    /* unbelievablelifespans.py SLOW_OK */
    SELECT
      cl_from
    FROM categorylinks
    WHERE cl_to = '%s_deaths';
    ''' % year)
    results = cursor.fetchall()
    for result in results:
        cl_from = int(result[0])
        death_years[cl_from] = year

def get_page_title_from_id(cursor, id):
    cursor.execute('''
    /* unbelievablelifespans.py SLOW_OK */
    SELECT
      page_namespace,
      ns_name,
      page_title
    FROM page
    JOIN toolserver.namespace
    ON dbname = %s
    AND page_namespace = ns_id
    WHERE page_id = %s;
    ''' , (settings.dbname, id))
    for row in cursor.fetchall():
        page_namespace = int(row[0])
        ns_name = unicode(row[1], 'utf-8')
        page_title = unicode(row[2], 'utf-8')
        if page_namespace in (6, 14):
            full_page_title = u'[[:'+ns_name+u':'+page_title+u']]'
        elif page_namespace in (0):
            full_page_title = u'[['+page_title+u']]'
        else:
            full_page_title = u'[['+ns_name+u':'+page_title+u']]'
    return full_page_title
    
i = 1
output = []
for k,v in birth_years.iteritems():
    page_id = k
    birth_year = v
    try:
        death_year = death_years[page_id]
    except KeyError:
        continue
    if (birth_year > death_year) or (death_year-birth_year > 115):
        page_title = get_page_title_from_id(cursor, page_id)
        table_row = u'''\
| %d
| %s
| %s
| %s
| %s
|-''' % (i, page_title, birth_year, death_year, death_year-birth_year)
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
