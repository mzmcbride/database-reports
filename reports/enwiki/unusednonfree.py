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
Report class for unused non-free files
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Unused non-free files'

    def get_preamble_template(self):
        return 'Unused non-free files; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['File']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* unusednonfree.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        JOIN categorylinks AS cl1
        ON cl1.cl_from = page_id
        LEFT JOIN imagelinks
        ON il_to = page_title
        AND page_namespace = 6
        LEFT JOIN categorylinks AS cl2
        ON cl2.cl_from = page_id
        AND cl2.cl_to = 'All_orphaned_non-free_use_Wikipedia_files'
        LEFT JOIN redirect
        ON rd_title = page_title
        AND rd_namespace = 6
        WHERE cl1.cl_to = 'All_non-free_media'
        AND il_from IS NULL
        AND cl2.cl_from IS NULL
        AND rd_from IS NULL
        AND page_is_redirect = 0
        AND page_namespace = 6;
        ''', (self.site, ))

        for ns_name, page_title in cursor:
            yield [u'[[:%s:%s|%s]]' % (ns_name, page_title, page_title)]

        cursor.close()
