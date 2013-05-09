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
Report class for shortest biographies of living people
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Shortest biographies of living people'

    def get_preamble_template(self):
        return u'''The shortest [[:Category:Living people|biographies of living people]] \
by page length in bytes (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Biography', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* shortestbios.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          page_len
        FROM page
        JOIN categorylinks
        ON cl_from = page_id
        WHERE page_namespace = 0
        AND page_is_redirect = 0
        AND cl_to = 'Living_people'
        ORDER BY 2, 1
        LIMIT 1000;
        ''')

        for page_title, page_len in cursor:
            yield [u'[[%s]]' % page_title, str(page_len)]

        cursor.close()
