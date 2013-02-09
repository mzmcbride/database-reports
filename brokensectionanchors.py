#!/usr/bin/python
# Public domain; MZMcBride; 2011

import ConfigParser
import datetime
import Levenshtein
import MySQLdb
import os
import re
import urllib
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

def get_article_section_anchors(article):
    # Returns a list of section anchors from a specified article
    article_sections = []
    # Set a user-agent :-)
    class urlopener(urllib.FancyURLopener):
        version = 'http://en.wikipedia.org/wiki/Wikipedia_talk:Database_reports'
    id_re = re.compile(r'id="(.+?)"')
    target_url = config.get('dbreps', 'apiurl').replace('w/api.php','wiki/%s' % article)
    urlopener = urlopener()
    page = urlopener.open(target_url)
    page_text = page.read()
    for match in id_re.finditer(page_text):
        article_sections.append(unescape_id(match.group(1).encode('utf-8')))
    return article_sections

def unescape_id(fragment):
    fragment = fragment.replace('%', 'UNIQUE MARKER')
    fragment = fragment.replace('.', '%')
    fragment = urllib.unquote(fragment)
    fragment = fragment.replace('%', '.')
    fragment = fragment.replace('UNIQUE MARKER', '%')
    return fragment

def get_top_edit_timestamp(cursor, page_id):
    cursor.execute('''
                   /* brokensectionanchors.py */
                   SELECT
                     MAX(rev_timestamp)
                   FROM revision
                   WHERE rev_page = %s;
                   ''' , page_id)
    return cursor.fetchone()[0]

def make_best_guess(fragment, anchors):
    transformed_fragment = fragment.lower().replace('-', '').replace('_', '')
    for anchor in anchors:
        try:
            decoded_anchor = anchor.decode('utf-8')
        except UnicodeDecodeError:
            decoded_anchor = u''
        transformed_anchor = decoded_anchor.lower().replace('-', '').replace('_', '')
        ratio = Levenshtein.ratio(transformed_anchor, transformed_fragment)
        if ratio > .8:
            return {'best_guess' : anchor, 'ratio': str(ratio)}
    return {'best_guess' : '', 'ratio': ''}

report_title = config.get('dbreps', 'rootpage') + 'Broken section anchors'

report_template = u'''\
Broken section anchors (limited to the first %s entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Redirect
! Best guess
! Ratio
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl')); wiki.setMaxlag(-1)
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

f = open('%sbroken-anchors-reviewed-page-ids.txt' % config.get('dbreps', 'path'), 'r')
reviewed_page_ids = f.read()
reviewed_page_ids_set = set(reviewed_page_ids.split('\n'))
f.close()

conn = MySQLdb.connect(host=config.get('dbreps', 'host')+'-user',
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('SET SESSION group_concat_max_len = 1000000;')
cursor.execute('''
               /* brokensectionanchors.py */
               SELECT
                 page_id,
                 rdr.rd_title AS target_title,
                 GROUP_CONCAT(CONCAT(page_id, '|', page_title, '|', rd.rd_fragment) SEPARATOR '\n') AS fragments
               FROM page
               JOIN redirect AS rdr
               ON rdr.rd_from = page_id
               JOIN u_mzmcbride_p.enwiki_redirects AS rd
               ON rd.rd_from = page_id
               WHERE page_namespace = 0
               AND rd.rd_fragment IS NOT NULL
               AND rd.rd_fragment NOT LIKE '%|%'
               AND rd.rd_title NOT LIKE '%|%'
               GROUP BY rd.rd_title
               LIMIT 10000;
               ''')

g = open('%sbroken-anchors-reviewed-page-ids.txt' % config.get('dbreps', 'path'), 'a')

i = 1
output = []
output_limit = 1000
recently_edited_pages = []
for row in cursor.fetchall():
    if i > output_limit:
        break
    fragments_dict = {}
    fragments = set()
    count = 0
    page_id = str(row[0])
    target_title = row[1]
    silly_values = row[2]
    for silly_value in silly_values.split('\n'):
        page_id_and_title = silly_value.rsplit('|', 1)[0]
        anchor = silly_value.rsplit('|', 1)[1]
        fragments_dict[anchor] = page_id_and_title
        fragments.add(anchor)
        silly_page_id = str(page_id_and_title.split('|', 1)[0])
        if int(get_top_edit_timestamp(cursor, silly_page_id)) > int(config.get('dbreps', 'dumpdate')+'000000'):
            recently_edited_pages.append(silly_page_id)
    if page_id not in reviewed_page_ids_set and page_id not in recently_edited_pages:
        real_anchors = get_article_section_anchors(target_title)
        for fragment in fragments:
            if i > output_limit:
                break
            if fragment in real_anchors:
                count += 1
            else:
                if not fragment:
                    fragment = ''
                else:
                    try:
                        fragment = unicode(fragment, 'utf-8')
                    except UnicodeDecodeError:
                        fragment = u'some craziness going on here'
                try:
                    redirect_title = unicode(fragments_dict[fragment.encode('utf-8')].split('|', 1)[1], 'utf-8')
                    redirect_id = fragments_dict[fragment.encode('utf-8')].split('|', 1)[0]
                except KeyError:
                    redirect_title = unicode(target_title, 'utf-8')
                    redirect_id = '-1'
                best_guess_dict = make_best_guess(fragment, real_anchors)
                best_guess = best_guess_dict['best_guess']
                ratio = best_guess_dict['ratio']
                table_row = u'''| %d
| {{dbr link|1=%s}}
| %s
| %s
|-''' % (i, redirect_title+u'#'+fragment, unicode(best_guess, 'utf-8'), unicode(ratio, 'utf-8'))
                if redirect_id not in recently_edited_pages:
                    output.append(table_row)
                    i += 1
    if count == len(fragments):
        g.write(page_id+'\n')

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
report_text = report_template % (output_limit, current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1, skipmd5=True)

cursor.close()
conn.close()
