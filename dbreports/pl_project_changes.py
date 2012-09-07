#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
 
# Copyright 2009-2011 bjweeks, MZMcBride, svick
 
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
import MySQLdb
import wikitools
import settings
import locale
import os
 
report_title = 'Wikipedia:Statystyki aktywności wikiprojektów'
 
report_template = u'''
Liczby zmian dokonanych na stronach i podstronach poszczególnych wikiprojektów w ciągu ostatnich 365 dni. \
Dane na dzień <onlyinclude>%s</onlyinclude>.
 
{| class="wikitable sortable plainlinks"
|-
! Lp.
! Wikiprojekt
! Edycje (z wyłączeniem stron dyskusji)
! Edycje (włącznie ze stronami dyskusji)
! Edycje (z wyłączeniem stron dyskusji, bez botów)
! Edycje (włącznie ze stronami dyskusji, bez botów)
|-
%s
|}

[[Kategoria:Wikiprojekty]]

[[en:Wikipedia:Database reports/WikiProjects by changes]]
'''
 
wiki = wikitools.Wiki('http://pl.wikipedia.org/w/api.php')
wiki.login(settings.username, settings.password)
 
conn = MySQLdb.connect(host='plwiki-p.rrdb.toolserver.org', db='plwiki_p', read_default_file='~/.my.cnf')
cursor = conn.cursor()
cursor.execute('''
/* pl_project_changes.py */
SELECT SUBSTRING_INDEX(page_title, '/', 1) AS project,
       SUM((
         SELECT COUNT(*)
         FROM revision
         WHERE page_id = rev_page
         AND page_namespace = 102
         AND DATEDIFF(NOW(), rev_timestamp) <= 365
       )) AS main_count,
       SUM((
         SELECT COUNT(*)
         FROM revision
         WHERE page_id = rev_page
         AND page_namespace = 103
         AND DATEDIFF(NOW(), rev_timestamp) <= 365
       )) AS talk_count,
       SUM((
         SELECT COUNT(*)
         FROM revision
         WHERE page_id = rev_page
         AND page_namespace = 102
         AND DATEDIFF(NOW(), rev_timestamp) <= 365
         AND rev_user NOT IN
          (SELECT ug_user
          FROM user_groups
          WHERE ug_group = 'bot')
       )) AS no_bots_main_count,
       SUM((
         SELECT COUNT(*)
         FROM revision
         WHERE page_id = rev_page
         AND page_namespace = 103
         AND DATEDIFF(NOW(), rev_timestamp) <= 365
         AND rev_user NOT IN
          (SELECT ug_user
          FROM user_groups
          WHERE ug_group = 'bot')
       )) AS no_bots_talk_count,
       (SELECT page_is_redirect
       FROM page
       WHERE page_namespace = 102
       AND page_title = project) AS redirect
FROM page
WHERE page_namespace BETWEEN 102 AND 103
AND page_is_redirect = 0
GROUP BY project
ORDER BY main_count DESC
''')
 
i = 1
output = []
for row in cursor.fetchall():
    page_title = unicode(row[0], 'utf-8').replace('_', ' ')
    page_link = '[[Wikiprojekt:%s|%s]]' % (page_title, page_title)
    main_edits = row[1]
    talk_edits = row[2]
    no_bots_main_edits = row[3]
    no_bots_talk_edits = row[4]
    is_redirect = row[5]
    if is_redirect:
        page_link = "''" + page_link + "''"
    table_row = u'''| %d
| %s
| %d
| %d
| %d
| %d
|-''' % (i, page_link, main_edits, talk_edits, no_bots_main_edits, no_bots_talk_edits)
    output.append(table_row)
    i += 1
 
locale.setlocale(locale.LC_ALL, 'pl')
os.environ['TZ'] = 'Europe/Warsaw'

cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.now() - datetime.timedelta(seconds=rep_lag)).strftime('%d %B %Y, %H:%M')
 
report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary='Aktualizacja', bot=1)
 
cursor.close()
conn.close()
