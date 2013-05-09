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
Report class for unprotected templates with many transclusions
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 1000

    def get_title(self):
        return 'Unprotected templates with many transclusions'

    def get_preamble_template(self):
        return u'Unprotected templates with many transclusions (over 500); data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Template', 'Transclusions']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* unprotectedtemps.py SLOW_OK */
        SELECT
          CONVERT(tl_title USING utf8),
          COUNT(*)
        FROM page
        JOIN templatelinks
        ON page_title = tl_title
        AND page_namespace = tl_namespace
        LEFT JOIN page_restrictions
        ON pr_page = page_id
        AND pr_level = 'sysop'
        AND pr_type = 'edit'
        WHERE tl_namespace = 10
        AND pr_page IS NULL
        GROUP BY tl_title
        HAVING COUNT(*) > 500
        ORDER BY COUNT(*) DESC;
        ''')

        for tl_title, count in cursor:
            tl_title = u'{{dbr link|1=%s}}' % tl_title
            yield [tl_title, str(count)]

        cursor.close()
