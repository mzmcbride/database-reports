# Copyright 2008, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for orphaned article deletion discussions
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Orphaned article deletion discussions'

    def get_preamble_template(self):
        return u'Subpages of [[Wikipedia:Articles for deletion]] that have no incoming links; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Page']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* orphanedafds.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8)
        FROM page
        LEFT JOIN pagelinks
        ON pl_title = page_title
        AND pl_namespace = page_namespace
        LEFT JOIN templatelinks
        ON tl_title = page_title
        AND tl_namespace = page_namespace
        WHERE page_namespace = 4
        AND page_is_redirect = 0
        AND page_title LIKE "Articles_for_deletion/%"
        AND ISNULL(pl_namespace)
        AND ISNULL(tl_namespace);
        ''')

        for (page_title, ) in cursor:
            yield [u'{{pllh|1=Wikipedia:%s}}' % page_title]

        cursor.close()
