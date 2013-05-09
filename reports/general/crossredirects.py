# Copyright 2008, 2013 bjweeks, MZMcBride, SQL, Tim Landscheidt

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
Report class for cross-namespace redirects
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Cross-namespace redirects'

    def get_preamble_template(self):
        return 'Cross-namespace redirects from (Main) to any other namespace; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Redirect', 'Target', 'Categorized?']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* crossredirects.py SLOW_OK */
        SELECT
          CONVERT(pt.page_namespace USING utf8),
          CONVERT(pf.page_title USING utf8),
          CONVERT(ns_name USING utf8),
          CONVERT(rd_title USING utf8),
          IF(EXISTS(SELECT TRUE FROM categorylinks
                      WHERE cl_from = pf.page_id
                      AND cl_to = 'Cross-namespace_redirects'),
             'Yes',
             'No')
            AS categorized
        FROM redirect, page AS pf, page AS pt
        JOIN toolserver.namespace
        ON pt.page_namespace = ns_id
        AND dbname = CONCAT(?, '_p')
        WHERE pf.page_namespace = 0
        AND rd_title = pt.page_title
        AND rd_namespace = pt.page_namespace
        AND pt.page_namespace != 0
        AND rd_from = pf.page_id
        AND pf.page_namespace = 0;
        ''', (self.site, ))

        for page_namespace, page_title, ns_name, rd_title, categorized in cursor:
            page_title = u'{{rlw|1=%s}}' % page_title
            rd_title = '{{plnr|1=%s:%s}}' % (ns_name, rd_title)
            yield [page_title, rd_title, categorized]

        cursor.close()
