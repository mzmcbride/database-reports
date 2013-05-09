# Copyright 2009, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for eponymous templates
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Eponymous templates'

    def get_preamble_template(self):
        return u'Eponymous templates; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Template', 'User']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        # Split query so that we don't trigger the query killer.
        for i in range(0, 1000):
            cursor.execute('''
            /* epontemps.py SLOW_OK */
            SELECT CONVERT(page_title USING utf8),
                   REPLACE(CONVERT(rev_user_text USING utf8), ' ', '_')
            FROM page
            JOIN revision ON rev_page = page_id
            WHERE page_id >=  ?      * 100000
              AND page_id <  (? + 1) * 100000
              AND page_namespace = 10
              AND rev_timestamp =
                (SELECT MIN(rev_timestamp)
                 FROM revision
                 WHERE rev_page = page_id)
              AND LENGTH(rev_user_text) > 1   -- utf8 doesn't matter here;
              AND INSTR(LOWER(CONVERT(page_title USING utf8)), REPLACE(LOWER(CONVERT(rev_user_text USING utf8)), ' ', '_')) <> 0;
            ''', (i, i))

            for page_title, rev_user_text in cursor:
                full_page_title = u'[[Template:%s|%s]]' % (page_title, page_title)
                full_rev_user_text = rev_user_text
                yield [full_page_title, full_rev_user_text]

        cursor.close()
