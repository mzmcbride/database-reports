# Copyright 2010, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for most-watched users
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Most-watched users'

    def get_preamble_template(self):
        return '''Most-watched users who currently have a non-redirect user talk page \
(limited to the first 1000 results); data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['User', 'Watchers']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* mostwatchedusers.py SLOW_OK */
        SELECT
          wl_title,
          COUNT(*)
        FROM watchlist
        JOIN page
        ON page_title = wl_title
        AND page_namespace = wl_namespace
        WHERE wl_namespace = 3
        AND wl_title NOT LIKE '%/%'
        AND page_is_redirect = 0
        GROUP BY wl_title
        ORDER BY COUNT(*) DESC
        LIMIT 1000;
        ''')

        for wl_title, watchers in cursor:
            yield [wl_title, str(watchers)]

        cursor.close()
