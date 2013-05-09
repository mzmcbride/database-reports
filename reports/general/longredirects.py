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
Report class for redirects obscuring page content
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Redirects obscuring page content'

    def get_preamble_template(self):
        return 'Redirects whose page length is greater than 449 bytes; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Redirect', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* longredirects.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          page_len
        FROM page
        JOIN toolserver.namespace
        ON page_namespace = ns_id
        AND dbname = CONCAT(?, '_p')
        WHERE page_is_redirect = 1
        HAVING page_len > 449
        ORDER BY page_namespace ASC;
        ''', (self.site, ))

        i = 1
        output = []
        for ns_name, page_title, page_len in cursor:
            if ns_name:
                page_title = '{{rle|1=%s:%s}}' % (ns_name, page_title)
            else:
                page_title = '{{rle|1=%s}}' % (page_title)
            yield [page_title, str(page_len)]

        cursor.close()
