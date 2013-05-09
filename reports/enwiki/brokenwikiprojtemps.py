# Copyright 2011, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for broken WikiProject templates
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Broken WikiProject templates'

    def get_preamble_template(self):
        return 'Broken WikiProject templates; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Template', 'Transclusions']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* brokenwikiprojtemps.py SLOW_OK */
        SELECT
          CONVERT(tl_title USING utf8),
          COUNT(*)
        FROM templatelinks
        JOIN page AS p1
        ON tl_from = p1.page_id
        LEFT JOIN page AS p2
        ON tl_namespace = p2.page_namespace
        AND tl_title = p2.page_title
        WHERE tl_namespace = 10
        AND tl_title LIKE 'Wiki%'
        AND tl_title RLIKE 'Wiki[_]?[Pp]roject.*'
        AND tl_title NOT LIKE '%/importance'
        AND tl_title NOT LIKE '%/class'
        AND p2.page_id IS NULL
        GROUP BY tl_title;
        ''')

        for page_title, transclusions in cursor:
            page_title = u'{{dbr link|1=%s}}' % page_title
            yield [page_title, str(transclusions)]

        cursor.close()
