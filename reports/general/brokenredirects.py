# Copyright 2008-2013 bjweeks, MZMcBride, SQL, Legoktm, Tim Landscheidt

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
Report class for broken redirects
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Broken redirects'

    def get_preamble_template(self):
        return 'Broken redirects; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Redirect']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* brokenredirects.py SLOW_OK */
        SELECT
          p1.page_namespace,
          CONVERT(ns_name USING utf8),
          CONVERT(p1.page_title USING utf8)
        FROM redirect AS rd
        JOIN page p1
        ON rd.rd_from = p1.page_id
        JOIN toolserver.namespace
        ON p1.page_namespace = ns_id
        AND dbname = CONCAT(?, '_p')
        LEFT JOIN page AS p2
        ON rd_namespace = p2.page_namespace
        AND rd_title = p2.page_title
        WHERE rd_namespace >= 0
        AND p2.page_namespace IS NULL
        ORDER BY p1.page_namespace ASC;
        ''' , (self.site, ))

        for page_namespace, ns_name, page_title in cursor:
            if page_namespace == 6 or page_namespace == 14:
                page_title = ':%s:%s' % (ns_name, page_title)
            elif ns_name:
                page_title = '%s:%s' % (ns_name, page_title)
            else:
                page_title = '%s' % (page_title)
            yield ['[[%s]]' % page_title]

        cursor.close()
