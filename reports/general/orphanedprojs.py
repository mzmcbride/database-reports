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
Report class for orphaned single-author project pages
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Orphaned single-author project pages'

    def get_preamble_template(self):
        return 'Orphaned single-author project pages; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Page']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* orphanedprojs.py SLOW_OK */
        SELECT DISTINCT
          CONVERT(ns_name USING utf8),
          CONVERT(pg1.page_title USING utf8)
        FROM page AS pg1
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND pg1.page_namespace = ns_id
        JOIN revision
        ON rev_page = pg1.page_id
        LEFT JOIN categorylinks
        ON cl_from = pg1.page_id
        LEFT JOIN pagelinks
        ON pl_from = pg1.page_id
        WHERE pg1.page_namespace = 4
        AND pg1.page_is_redirect = 0
        AND cl_from IS NULL
        AND (SELECT
               COUNT(DISTINCT rev_user_text)
             FROM revision
             WHERE rev_page = pg1.page_id) = 1
        AND (SELECT
               COUNT(*)
             FROM page AS pg2
             LEFT JOIN pagelinks AS pltmp
             ON pg2.page_id = pltmp.pl_from
             WHERE pltmp.pl_title = pg1.page_title
             AND pltmp.pl_namespace = pg1.page_namespace
             AND pg2.page_namespace = 4) = 0
        AND NOT EXISTS (SELECT
                          1
                        FROM templatelinks
                        JOIN page AS pg3
                        ON tl_from = pg3.page_id
                        WHERE tl_namespace = 4
                        AND tl_title = pg1.page_title
                        AND pg3.page_namespace = 4)
        LIMIT 1000;
        ''', (self.site, ))

        for ns_name, page_title in cursor:
            page_title = u'{{pllh|1=%s:%s}}' % (ns_name, page_title)
            yield [page_title]

        cursor.close()
