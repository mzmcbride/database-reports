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
Report class for untagged biographies of living people
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Untagged biographies of living people'

    def get_preamble_template(self):
        return u'''Pages in [[:Category:Living people]] missing WikiProject tags (limited to \
the first 1000 entries); data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Biography']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* untaggedblps.py SLOW_OK */
        SELECT
          CONVERT(p1.page_title USING utf8)
        FROM page AS p1
        JOIN categorylinks
        ON cl_from = p1.page_id
        WHERE cl_to = 'Living_people'
        AND p1.page_namespace = 0
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS p2
                        WHERE p2.page_title = p1.page_title
                        AND p2.page_namespace = 1)
        LIMIT 1000;
        ''')

        for (page_title, ) in cursor:
            yield [u'[[%s]]' % page_title]

        cursor.close()
