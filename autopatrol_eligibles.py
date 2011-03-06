#!/usr/bin/env python2.5
 
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
 
import datetime
import dateutil.relativedelta
import MySQLdb
import re
import wikitools
import settings
 
report_title = settings.rootpage + 'Editors eligible for Autopatrol privilege'
 
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
 
wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)
 
conn = MySQLdb.connect(host=settings.host, db=settings.dbname, read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* autopatrol_eligibles.py */
select user_name
  from user_groups
  join user on user_id = ug_user
  where ug_group in ('sysop', 'autoreviewer', 'bot')
''')
excluded = set([unicode(x[0], 'utf-8') for x in cursor.fetchall()])

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
select page_creator as user, count(*) as count
  from u_mzmcbride_enwiki_page_creators_p.page as pc
  join page on pc.page_id = page.page_id
  where page_namespace = 0 
    and page_is_redirect = 0 
  group by page_creator
  having count >= 50
  order by count desc;
''')
 
i = 1
output = []
for row in cursor.fetchall():
    user_name = unicode(row[0], 'utf-8')
    if user_name in excluded:
        continue

    cursor = conn.cursor()
    cursor.execute('''
/* autopatrol_eligibles.py */
select user_name
  from user
  where user_name = %s
    and user_id in
      (select rev_user
        from revision
        where rev_timestamp > date_format(adddate(now(), -30), '%%Y%%m%%d%%H%%i%%s'))
    and user_registration < date_format(adddate(now(), -180), '%%Y%%m%%d%%H%%i%%s')
    and user_id not in
      (select ipb_user from ipblocks
        where ipb_range_end = '')
''', row[0])
    if not cursor.fetchone():
        continue

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
report.edit(report_text, summary=settings.editsumm, bot=1)
 
cursor.close()
conn.close()
