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
import dateutil.relativedelta
import MySQLdb
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Editors eligible for Autopatrol privilege'

report_template = u'''
Below is a list of editors who are eligible for the autopatrol privilege and don't have it yet; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks"
|-
! No.
! Username
! Articles created
|-
%s
|}

[[Category:Wikipedia database reports|Editors eligible for Autopatrol privilege]]
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'), db=config.get('dbreps', 'dbname'), read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* autopatrol_eligibles.py */
select ug_user
  from user_groups
  where ug_group in ('sysop', 'autoreviewer', 'bot')
''')
excluded = set([x[0] for x in cursor.fetchall()])

this_month = datetime.date.today()
last_month = this_month - dateutil.relativedelta.relativedelta(months = 1)
for month in [last_month, this_month]:
  page_name = 'Wikipedia:Requests for permissions/Denied/' + month.strftime('%B %Y')
  page = wikitools.Page(wiki, page_name)
  page_text = page.getWikiText()
  matches = re.findall('^\*{{Usercheck-short\|(.*)}} \[\[Wikipedia:Requests for permissions/Autopatrolled\]\]', page_text, re.M)
  for match in matches:
    user_name = match[0].capitalize() + match[1:]
    excluded.add(user_name)

cursor = conn.cursor()
cursor.execute('''
/* autopatrol_eligibles.py */
/* SLOW_OK */
select c_user_id as user, count(*) as count, max(c_timestamp) as last_creation
  from u_svick_enwiki_page_creators_p.creator as pc
  join page on c_page_id = page_id
  where page_namespace = 0
    and page_is_redirect = 0
  group by user
  having count >= 50
  and last_creation > date_format(adddate(now(), -30), '%Y%m%d%H%i%s')
  order by count desc;
''')

i = 1
output = []
for row in cursor.fetchall():
    user_id = row[0]
    if user_id in excluded:
        continue

    cursor = conn.cursor()
    cursor.execute('''
/* autopatrol_eligibles.py */
select user_name
  from user
  where user_id = %s
    and user_registration < date_format(adddate(now(), -180), '%%Y%%m%%d%%H%%i%%s')
    and user_id not in
      (select ipb_user from ipblocks
        where ipb_range_end = '')
''', row[0])
    name_row = cursor.fetchone()
    if not name_row:
        continue

    user_name = unicode(name_row[0], 'utf-8')
    page_title = '[[User:%s|%s]]' % (user_name, user_name)
    count = row[1]
    table_row = u'''| %d
| %s
| %d
|-''' % (i, page_title, count)
    output.append(table_row)
    i += 1

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
