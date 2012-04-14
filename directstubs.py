#! /usr/bin/env python
# Public domain; MZMcBride; 2012

from __future__ import generators
import datetime
import math
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Stubs included directly in stub categories/%i'

report_template = u'''\
Stubs included directly in stub categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
%s
|}
'''

rows_per_page = 800

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

target_cat = 'Stub_categories'
master_dict = {}

def get_subcats(cursor, cat):
    global master_dict
    results = []
    cursor.execute('''
    /* directstubs.py */
    SELECT
      page_title
    FROM page
    JOIN categorylinks
    ON cl_from = page_id
    WHERE cl_to = %s
    AND page_namespace = 14;
    ''' , cat)
    rows = cursor.fetchall()
    for row in rows:
        results.append(row[0])
    try:
        master_dict[cat] = results
    except KeyError:
        return False
    return results

def walk_tree(cursor, target_cat):
    subcats = get_subcats(cursor, target_cat)
    for subcat in subcats:
        if subcat not in master_dict.keys():
            for subsubcat in walk_tree(cursor, subcat):
                yield subsubcat, subcats
        else:
            yield subcat, subcats

def get_stub_template_redirects(cursor, template):
    template_redirects = []
    cursor.execute('''
    /* directstubs.py */
    SELECT
      page_title
    FROM page
    JOIN redirect
    ON rd_from = page_id
    WHERE rd_title = %s
    AND rd_namespace = 10
    AND page_namespace = 10;
    ''' , template)
    for row in cursor.fetchall():
        template_redirects.append(row[0])
    return template_redirects

def get_stub_templates_from_category(cursor, entry):
    templates = []
    cursor.execute('''
    /* directstubs.py */
    SELECT
      page_title
    FROM page
    JOIN categorylinks
    ON cl_from = page_id
    WHERE page_namespace = 10
    AND cl_to = %s;
    ''' , entry)
    for row in cursor.fetchall():
        template_name = row[0]
        templates.append(template_name)
        for template_redirect in get_stub_template_redirects(cursor, template_name):
            templates.append(template_redirect)
    return templates

def get_articles_from_category(cursor, entry):
    articles = []
    cursor.execute('''
    /* directstubs.py */
    SELECT
      page_title
    FROM page
    JOIN categorylinks
    ON cl_from = page_id
    WHERE page_namespace = 0
    AND page_is_redirect = 0
    AND cl_to = %s;
    ''' , entry)
    for row in cursor.fetchall():
        articles.append(row[0])
    if articles:
        return articles
    return False

def get_stub_templates_from_article(cursor, article):
    stub_templates_from_article = []
    cursor.execute('''
    /* directstubs.py */
    SELECT
      tl_title
    FROM page
    JOIN templatelinks
    ON tl_from = page_id
    WHERE page_namespace = 0
    AND page_title = %s;
    ''' , article)
    for row in cursor.fetchall():
        if row[0].endswith('-stub'):
            stub_templates_from_article.append(row[0])
    return stub_templates_from_article

conn = MySQLdb.connect(host=settings.host,
                       db=settings.dbname,
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()

for hello in walk_tree(cursor, target_cat):
    # Surely there's a better way to do this
    here = 'silliness'

all_cats_from_target_cat = set()
for k in master_dict.keys():
    all_cats_from_target_cat.add(k)

i = 1
output = []
for entry in all_cats_from_target_cat:
    category_stub_templates = get_stub_templates_from_category(cursor, entry)
    category_articles = get_articles_from_category(cursor, entry)
    if category_articles:
        for member in category_articles:
            found = False
            stub_templates_in_article = get_stub_templates_from_article(cursor, member)
            for stub_template in stub_templates_in_article:
                if stub_template in category_stub_templates:
                    found = True
            if not found:
                page_title = u'[[%s]]' % unicode(member, 'utf-8')
                table_row = u'''|-
| %d
| %s''' % (i, page_title)
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
    report.edit(report_text, summary=settings.editsumm, bot=1)
    page += 1
    end += rows_per_page

page = math.ceil(len(output) / float(rows_per_page)) + 1
while 1:
    report = wikitools.Page(wiki, report_title % page)
    report_text = settings.blankcontent
    report_text = report_text.encode('utf-8')
    if not report.exists:
        break
    report.edit(report_text, summary=settings.blanksumm, bot=1)
    page += 1

cursor.close()
conn.close()
