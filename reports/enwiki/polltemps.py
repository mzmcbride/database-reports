# Copyright 2011, 2013 bjweeks, MZMcBride, WOSlinker, Tim Landscheidt

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
Report class for template categories containing articles
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Template categories containing articles'

    def get_preamble_template(self):
        return 'Template categories containing articles; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Category']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* polltemps.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8)
        FROM page AS pg1
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND pg1.page_namespace = ns_id
        JOIN templatelinks AS tl
        ON pg1.page_id = tl.tl_from
        WHERE pg1.page_namespace = 14
        AND tl.tl_namespace = 10
        AND tl.tl_title = 'Template_category'
        AND EXISTS (SELECT
                      1
                    FROM page AS pg2
                    JOIN categorylinks AS cl
                    ON pg2.page_id = cl.cl_from
                    WHERE pg2.page_namespace = 0
                    AND pg1.page_title = cl.cl_to);
        ''', (self.site, ))

        for ns_name, cl_to in cursor:
            yield [u'[[:%s:%s|%s]]' % (ns_name, cl_to, cl_to)]

        cursor.close()
