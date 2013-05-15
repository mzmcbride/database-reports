# -*- coding: utf-8 -*-

# Copyright 2009-2011, 2013 bjweeks, MZMcBride, svick, Tim Landscheidt

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

"""
Report class for Polish WikiProjects by changes
"""

import reports

class report(reports.report):
    def get_title(self):
        return u'Statystyki aktywności wikiprojektów'

    def get_preamble_template(self):
        return u'''Liczby zmian dokonanych na stronach i podstronach poszczególnych wikiprojektów w ciągu ostatnich 365 dni. \
Dane na dzień <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return [u'Wikiprojekt',
                u'Edycje (z wyłączeniem stron dyskusji)',
                u'Edycje (włącznie ze stronami dyskusji)',
                u'Edycje (z wyłączeniem stron dyskusji, bez botów)',
                u'Edycje (włącznie ze stronami dyskusji, bez botów)']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* pl_project_changes.py SLOW_OK */
        SELECT CONVERT(SUBSTRING_INDEX(page_title, '/', 1) USING utf8) AS project,
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

        for page_title, main_edits, talk_edits, no_bots_main_edits, no_bots_talk_edits, is_redirect in cursor:
            page_title = page_title.replace('_', ' ')
            page_link = u'[[Wikiprojekt:%s|%s]]' % (page_title, page_title)
            if is_redirect:
                page_link = u"''%s''" % page_link
            yield [page_link, str(main_edits), str(talk_edits), str(no_bots_main_edits), str(no_bots_talk_edits)]

        cursor.close()

    def get_footer(self):
        return u'''[[Kategoria:Wikiprojekty]]

[[en:Wikipedia:Database reports/WikiProjects by changes]]'''
