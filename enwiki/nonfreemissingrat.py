#!/usr/bin/python
# Public domain; MZMcBride; 2012

import ConfigParser
import datetime
import MySQLdb
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Non-free files missing a rationale'

report_template = u'''
Non-free files missing a [[WP:FUR|fair use rationale]] (limited to the first \
2000 entries); data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! File
! Length
! Uploader
|-
%s
|}
'''

fair_use_strings = [
r'=.*(fair[ -]?use|non[ -]?free|rationale).*=',
r'rationale for the fair use',
r'qualifies as fair use',
r'fair use in \[\[',
r'\'\'\'fair use rationale[:]?\'\'\'',
r'the doctrine of fair use',
r'the purpose of this image',
r'this low quality image',
r'use of this image will not decrease',
r'conforms with the requirements',
r'is a low resolution screenshot'
r'is a low resolution of the original',
r'used here for purely encyclopedic and informational purposes',
r'use of this low-resolution version',
r'does not in any way limit the ability of the copyright',
r'rationale for use on',
r'image is suitable for fair use on',
r'is a low resolution copy of the original',
r'rationale:',
r'is only being used for informational purposes',
r'constitutes fair use',
r'does not deprive the owner of any revenue',
r'no free substitute can be made',
r'does not limit the copyright owner\'s rights',
r'within fair use guidelines',
r'fair use rationale:',
r'qualifies for fair use',
r'is a low-resolution image',
r'image is being used to illustrate',
r'Fair Use Rationale for',
r'for the purposes of criticism and comment',
r'contributes to the article significantly',
r'does not limit the copyright owner\'s ability',
r'no free equivalent is available',
r'does not limit the copyright holder\'s ability',
r'enhances the article in which it\'s displayed',
r'falls under fair use as',
r'will not limit the .+ ability',
r'a historically significant photo',
r'much lower resolution than the original',
r'image is of low size and quality',
r'used under a claim of fair use',
r'used for the educational purposes',
r'only for educational purposes and is not used for profit',
r'depicts a.+historic event',
r'quality of the image is very low',
r'Purpose is purely informational',
r'considerably lower resolution than the original',
r'where no new free-use image is available',
r'solely for the purpose of illustration',
r'allow use of this image to illustrate articles',
r'{{MTG set symbol}}',
r'{{\s*standard[\s-]*rationale',
r'{{\s*short[\s-]*rationale',
r'unable to find a suitable free replacement',
r'for critical commentary and discussion of',
r'no free version is available',
r'is of lower resolution than the original',
r'does not limit the copyright owners\' rights',
r'does not limit the copyright holder\'s rights',
r'no adequate free alternative available',
r'no known free replacement is available',
r'{{\s*Non-free Wikimedia logo',
r'{{\s*Wikimedia logo',
r'{{\s*Copyright by Wikimedia',
r'{{\s*Wikipedia[\s-]*screenshot',
r'low-res(olution)? (\'\'\')?promotional(\'\'\')? (image|file)'
]

find_fair_use_strings = re.compile(r'(%s)' % '|'.join(str(i) for i in fair_use_strings), re.I)

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl')); wiki.setMaxlag(-1)
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* nonfreemissingrat.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN categorylinks
ON cl_from = page_id
WHERE page_namespace = 10
AND cl_to = 'Wikipedia_non-free_file_copyright_tags';
''')
copyright_templates = cursor.fetchall()

files_using_fair_use_copyright_templates = set()
for result in copyright_templates:
    template = result[0]
    cursor.execute('''
    /* nonfreemissingrat.py SLOW_OK */
    SELECT
      page_id
    FROM page
    JOIN templatelinks
    ON tl_from = page_id
    WHERE tl_namespace = 10
    AND tl_title = %s
    AND page_namespace = 6;
    ''' , template)
    rows = cursor.fetchall()
    for row in rows:
        page_id = int(row[0])
        files_using_fair_use_copyright_templates.add(page_id)

cursor.execute('''
/* nonfreemissingrat.py SLOW_OK */
SELECT
  page_title
FROM page
JOIN categorylinks
ON cl_from = page_id
WHERE page_namespace = 10
AND cl_to = 'Non-free_use_rationale_templates';
''')
fair_use_templates = cursor.fetchall()

files_using_fair_use_templates = set()
for result in fair_use_templates:
    template = result[0]
    cursor.execute('''
    /* nonfreemissingrat.py SLOW_OK */
    SELECT
      page_id
    FROM page
    JOIN templatelinks
    ON tl_from = page_id
    WHERE tl_namespace = 10
    AND tl_title = %s
    AND page_namespace = 6;
    ''' , template)
    rows = cursor.fetchall()
    for row in rows:
        page_id = int(row[0])
        files_using_fair_use_templates.add(page_id)

reviewed_page_ids = set()
f = open('%snonfree-reviewed-page-ids.txt' % config.get('dbreps', 'path'), 'r')
file_contents = f.read()
for line in file_contents.split('\n'):
    if line:
        reviewed_page_ids.add(int(line))
f.close()

pages_to_check = (files_using_fair_use_copyright_templates -
                  files_using_fair_use_templates -
                  reviewed_page_ids)

i = 1
output = []
g = open('%snonfree-reviewed-page-ids.txt' % config.get('dbreps', 'path'), 'a')
for id in pages_to_check:
    if i > 2000:
        break
    cursor.execute('''
    /* nonfreemissingrat.py SLOW_OK */
    SELECT
      page_title,
      page_len
    FROM page
    WHERE page_id = %s;
    ''' , id)
    data = cursor.fetchall()
    if not data:
        continue
    cursor.execute('''
    /* nonfreemissingrat.py SLOW_OK */
    SELECT
      img_user_text
    FROM image
    JOIN page
    ON img_name = page_title
    AND page_namespace = 6
    WHERE page_id = %s
    ORDER BY img_timestamp ASC
    LIMIT 1;
    ''' , id)
    record = cursor.fetchone()
    if record:
        img_user_text = u'[[User:%s|%s]]' % (unicode(record[0], 'utf-8'),
                                             unicode(record[0], 'utf-8'))
    for d in data:
        page_title = d[0]
        page_len = d[1]
    page = wikitools.Page(wiki, 'File:%s' % page_title, followRedir=False)
    try:
        page_text = page.getWikiText()
    except wikitools.page.NoPage:
        continue
    if not find_fair_use_strings.search(page_text):
        page_title = unicode(page_title, 'utf-8')
        table_row = u'''\
| %d
| [[:File:%s|%s]]
| %s
| %s
|-''' % (i, page_title, page_title, page_len, img_user_text)
        output.append(table_row)
        i += 1
    else:
        g.write('%s\n' % id)
g.close()

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
