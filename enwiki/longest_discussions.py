#!/usr/bin/python

# Copyright 2009-2010 bjweeks, MZMcBride, svick

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

report_title = config.get('dbreps', 'rootpage') + 'Talk pages by size'

report_template = u'''
:''For talk pages whose page length is greater than 140,000 bytes (excluding subpages and pages in the user space), see [[Wikipedia:Database reports/Long pages|Database reports/Long pages]].''

\'''Database reports/Talk pages by size\''' provides a ranked tally of the total size of a given talk page, including all its subpages (e.g. [[Help:Archiving a talk page|archival subpages]] for a user talk page, individual {{abbrlink|WP:RFA|WP:Requests for adminship}}<nowiki>s</nowiki>, etc.), to provide statistics on very active discussion pages. It is a ''statistical report'' for information only<!--i.e no call to action; added per MfD-->; please see [[Wikipedia:Database reports|Database reports]] for the distinction between the two report types. It was created in response to a community member {{scp |url=http://en.wikipedia.org/w/index.php?title=WT:Database_reports&oldid=398581037#List_of_longest_.27DISCUSSION.27_content. |name=request}}, and is [[User:SvickBOT|bot]]-generated.

Below is a list of talk pages by their total size, including subpages; data as of <onlyinclude>%s</onlyinclude>.

== Article talk pages ==

{| class="wikitable sortable plainlinks"
|-
! No.
! Page
! Size [MB]
|-
%s
|}

== Other talk pages ==

{| class="wikitable sortable plainlinks"
|-
! No.
! Page
! Size [MB]
|-
%s
|}

==See also==
* [[Wikipedia:Don't worry about performance|Don't worry about performance]]

[[Category:Wikipedia database reports|Talk pages by size]]
[[Category:Wikipedia statistics|Talk pages by size]]
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* longest_discussions.py */
/* SLOW_OK */
SELECT
	'Talk' AS ns_name,
	REPLACE(SUBSTRING_INDEX(page_title, '/', 1), '_', ' ') AS parent,
	SUM(page_len) / 1024 / 1024 AS total_size
FROM page
WHERE page_namespace = 1
GROUP BY page_namespace, parent
ORDER BY total_size DESC
LIMIT 100
''')

i = 1
article_talks = []
for row in cursor.fetchall():
    page_title = '[[%s:%s]]' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'))
    if row[1] == '9':
      page_title = page_title + ' <small>(including [[Special:PrefixIndex/Talk:9/11|all pages beginning with Talk:9/11]])</small>'
    size = row[2]
    table_row = u'''| %d
| %s
| %.1f
|-''' % (i, page_title, size)
    article_talks.append(table_row)
    i += 1

cursor.execute('''
/* longest_discussions.py */
/* SLOW_OK */
SELECT
  ns_name,
  REPLACE(SUBSTRING_INDEX(page_title, '/', 1), '_', ' ') AS parent,
  SUM(page_len) / 1024 / 1024 AS total_size
FROM page
JOIN toolserver.namespacename ON ns_id = page_namespace
WHERE page_namespace MOD 2 = 1
AND page_namespace != 1
AND dbname = 'enwiki_p'
AND ns_is_favorite = 1
GROUP BY page_namespace, parent
ORDER BY total_size DESC
LIMIT 200
''')

i = 1
other_talks = []
for row in cursor.fetchall():
    page_title = '[[%s:%s]]' % (unicode(row[0], 'utf-8'), unicode(row[1], 'utf-8'))
    size = row[2]
    table_row = u'''| %d
| %s
| %.1f
|-''' % (i, page_title, size)
    other_talks.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(article_talks), '\n'.join(other_talks))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
