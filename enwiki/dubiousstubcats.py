#!/usr/bin/python
# Public domain; MZMcBride; 2012

from __future__ import generators
import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Dubious stub categories'

report_template = u'''\
Dubious stub categories; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Category
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

target_cat = 'Stub_categories'
master_dict = {}

def get_subcats(cursor, cat):
    global master_dict
    results = []
    cursor.execute('''
    /* dubiousstubcats.py */
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

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
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
for member in all_cats_from_target_cat:
    if not member.endswith('_stubs'):
        cat_title = u'[[:Category:%s|%s]]' % (unicode(member, 'utf-8'),
                                              unicode(member, 'utf-8'))
        table_row = u'''|-
| %d
| %s''' % (i, cat_title)
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
