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
Report class for user template redirects
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'User template redirects'

    def get_preamble_template(self):
        return '''Pages in the Template namespace that redirect to the User namespace; \
        data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Template', 'Target']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* usertempreds.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          CONVERT(rd_title USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND ns_id = page_namespace
        JOIN redirect
        ON rd_from = page_id
        WHERE rd_namespace = 2
        AND page_namespace = 10;
        ''', (self.site, ))

        for ns_name, page_title, rd_title in cursor.fetchall():
            full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
            full_rd_title = u'[[User:%s]]' % (rd_title)
            yield [full_page_title, full_rd_title]

        cursor.close()
