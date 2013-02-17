#!/usr/bin/python

# Copyright 2008 bjweeks, MZMcBride

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
import operator
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Users by log action'

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf', use_unicode=True)
cursor = conn.cursor()

def get_stats(type, action):
    cursor.execute(u'''
    /* logactions.py SLOW_OK */
    SELECT
      user_name,
      COUNT(log_timestamp)
    FROM logging
    JOIN user_ids
    ON user_id = log_user
    WHERE log_type = '%s'
    AND log_action = '%s'
    GROUP BY log_user;
    ''' % (type, action))
    return cursor.fetchall()

query_list = [
    {'name': 'Deletions',                 'short_name': 'DL', 'type': 'delete',     'action': 'delete'},
    {'name': 'Undeletions',               'short_name': 'UD', 'type': 'delete',     'action': 'restore'},
    {'name': 'Revision deletions',        'short_name': 'RD', 'type': 'delete',     'action': 'revision'},
    {'name': 'Event deletions',           'short_name': 'ED', 'type': 'delete',     'action': 'event'},
    {'name': 'Deletion suppressions',     'short_name': 'DS', 'type': 'suppress',   'action': 'delete'},
    {'name': 'Revision suppressions',     'short_name': 'RS', 'type': 'suppress',   'action': 'revision'},
    {'name': 'Event suppressions',        'short_name': 'ES', 'type': 'suppress',   'action': 'event'},
    {'name': 'Username suppressions',     'short_name': 'US', 'type': 'suppress',   'action': 'reblock'},
    {'name': 'Protections',               'short_name': 'PT', 'type': 'protect',    'action': 'protect'},
    {'name': 'Unprotections',             'short_name': 'UP', 'type': 'protect',    'action': 'unprotect'},
    {'name': 'Protection modifications',  'short_name': 'PM', 'type': 'protect',    'action': 'modify'},
    {'name': 'Blocks',                    'short_name': 'BL', 'type': 'block',      'action': 'block'},
    {'name': 'Unblocks',                  'short_name': 'UB', 'type': 'block',      'action': 'unblock'},
    {'name': 'Block modifications',       'short_name': 'BM', 'type': 'block',      'action': 'reblock'},
    {'name': 'User renames',              'short_name': 'UR', 'type': 'renameuser', 'action': 'renameuser'},
    {'name': 'User rights modifications', 'short_name': 'RM', 'type': 'rights',     'action': 'rights'},
    {'name': 'Whitelistings',             'short_name': 'WL', 'type': 'gblblock',   'action': 'whitelist'},
    {'name': 'De-whitelistings',          'short_name': 'DW', 'type': 'gblblock',   'action': 'dwhitelist'},
#    {'name': 'AbuseFilter modifications', 'short_name': 'AM', 'type': 'abusefilte', 'action': 'modify'}
]
user_stats = {}

for query in query_list:
    stats_query = get_stats(query['type'], query['action'])
    query['len'] = len(stats_query)
    for row in stats_query:
        user = unicode(row[0], 'utf-8')
        count = row[1]
        if user not in user_stats:
            user_stats[user] = {query['name']: count}
        else:
            user_stats[user][query['name']] = count

output = u''

report_template = u'{{shortcut|WP:LOGACTIONS}}\nUsers by log action; data as of <onlyinclude>%s</onlyinclude>.\n%s'

table_template = u'''
== %s ==
{| class="wikitable sortable" style="width:23em;"
|- style="white-space:nowrap;"
!No.
!User
!Count
|-
%s
|}
'''

for query in query_list:
    stat_dict = {}
    for user,stats in user_stats.iteritems():
        if query['name'] in stats:
            stat_dict[user] = stats[query['name']]
    stats = sorted(stat_dict.iteritems(), key=operator.itemgetter(1), reverse=True)[0:25]
    rows = []
    i = 1
    for user, count in stats:
        rows.append(u'''|%d||%s||%s\n|-''' % (i, user, count))
        i += 1
    output += table_template % (query['name'], '\n'.join(rows))
    if query['len'] > 25:
        output += "Full results are available [[{{FULLPAGENAME}}#Totals|below]].\n"

master_table_template = u'''
== Totals ==
Hover over the abbreviations to see the full action name.

{| class="wikitable sortable" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
!No.
!User
%s
!Total
|-
%s class="sortbottom"
!colspan="2"|Totals
%s
|}
'''

new_query_list = []

for query in query_list:
    if query['len'] > 25:
        new_query_list.append(query)

query_list = new_query_list

rows = []
totals = dict([(query['name'], 0) for query in query_list])
totals['total'] = 0
i = 1
user_stats_sorted = sorted(user_stats.iteritems(), key=operator.itemgetter(0))
for user,stats in user_stats_sorted:
    row = []
    total = 0
    row.append(str(i))
    row.append(user)
    for query in query_list:
        if query['name'] in stats:
            row.append(str(stats[query['name']]))
            total += stats[query['name']]
            totals[query['name']] += stats[query['name']]
            totals['total'] += stats[query['name']]
        else:
            row.append('0')
    row.append(str(total))
    rows.append('|%s\n|-' % ('||'.join(row)))
    i += 1

output += master_table_template % (
    '\n'.join(['!<span title="%s">%s</span>' % (query['name'], query['short_name']) for query in query_list]),
    '\n'.join(rows),
    '\n'.join([u'!style="text-align:left;"|%d' % totals[query['name']] for query in query_list]) + u'\n!style="text-align:left;"|%d' % totals['total']
)

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

final_output = report_template % (current_of, output)
final_output = final_output.encode('utf-8')
report = wikitools.Page(wiki, report_title)
report.edit(final_output, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
