#!/usr/bin/python

# Copyright 2010 bjweeks, MZMcBride

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Most-watched pages by namespace'

report_template = u'''
Most-watched non-deleted pages by namespace. Limited to the first 100 entries per \
namespace and pages with fewer than 30 watchers have their count redacted; \
data as of <onlyinclude>%s</onlyinclude>.
%s
'''

report_section = u'''
== %s / %s ==
{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! style="width:10%%;" | No.
! Page
! style="width:10%%;" | Watchers
|-
%s
|}\
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

def namespace_names(cursor, dbname):
    nsdict = {}
    cursor.execute('''
    /* mostwatchedperns.py namespace_names */
    SELECT
      ns_id,
      ns_name
    FROM toolserver.namespace
    WHERE dbname = %s
    AND ns_id >= 0
    ORDER BY ns_id ASC;
    ''', config.get('dbreps', 'dbname'))
    for row in cursor.fetchall():
        ns_id = row[0]
        ns_name = unicode(row[1], 'utf-8')
        nsdict[ns_id] = ns_name
    return nsdict

def get_top_pages(cursor, namespace):
    cursor.execute('''
    /* mostwatchedperns.py top_pages */
    SELECT
      wl_title,
      COUNT(*)
    FROM watchlist
    JOIN page
    ON wl_namespace = page_namespace
    AND wl_title = page_title
    WHERE wl_namespace = %s
    GROUP BY wl_title
    ORDER BY COUNT(*) DESC, wl_title ASC
    LIMIT 100;
    ''', namespace)
    top_pages = []
    i = 1
    for row in cursor.fetchall():
        page_title = u'%s' % unicode(row[0], 'utf-8')
        if namespace == 6 or namespace == 14:
            page_title = '[[:%s:%s]]' % (nsdict[namespace], page_title)
        elif namespace == 0:
            page_title = '[[%s]]' % (page_title)
        else:
            page_title = '[[%s:%s]]' % (nsdict[namespace], page_title)
        watchers = row[1]
        if int(watchers) < 30:
            watchers = '&mdash;'
        table_row = u'''| %d
| %s
| %s
|-''' % (i, page_title, watchers)
        top_pages.append(table_row)
        i += 1
    if nsdict[namespace] == '':
        subject_namespace = '(Main)'
    else:
        subject_namespace = nsdict[namespace]
    talk_namespace = nsdict[namespace+1]
    return report_section % (subject_namespace, talk_namespace, '\n'.join(top_pages))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
nsdict = namespace_names(cursor, config.get('dbreps', 'dbname'))
i = 1
output = []
for k,v in nsdict.iteritems():
    if int(k) % 2 == 0:
        output.append(get_top_pages(cursor, k))

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
