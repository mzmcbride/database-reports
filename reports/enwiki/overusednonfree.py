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
Report class for overused non-free files
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Overused non-free files'

    def get_preamble_template(self):
        return 'Non-free files used on more than four pages; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['File', 'Uses']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* overusednonfree.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          COUNT(*)
        FROM imagelinks
        JOIN (SELECT
                page_id,
                ns_name,
                page_title
              FROM page
              JOIN toolserver.namespace
              ON dbname = CONCAT(?, '_p')
              AND page_namespace = ns_id
              JOIN categorylinks
              ON cl_from = page_id
              WHERE cl_to = 'All_non-free_media'
              AND page_namespace = 6) AS pgtmp
        ON pgtmp.page_title = il_to
        GROUP BY il_to
        HAVING COUNT(*) > 4
        ORDER BY COUNT(*) ASC;
        ''', (self.site, ))

        for ns_name, page_title, count in cursor:
            page_title = u'[[:%s:%s|%s]]' % (ns_name, page_title, page_title)
            yield [page_title, str(count)]

        cursor.close()
