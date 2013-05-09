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
Report class for transplanted user templates
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Transplanted user templates'

    def get_preamble_template(self):
        return u'User templates used in the (Main) or Template namespaces; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Template', 'Page']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* transusertemps.py SLOW_OK */
        SELECT
          CONVERT(tl_title USING utf8),
          page_namespace,
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND ns_id = page_namespace
        JOIN templatelinks
        ON tl_from = page_id
        WHERE page_namespace IN (0,10)
        AND tl_namespace = 2;
        ''', (self.site, ))

        for tl_title, page_namespace, ns_name, page_title in cursor:
            full_tl_title = u'[[User:%s]]' % (tl_title)
            if page_namespace == 10:
                full_page_title = u'[[%s:%s]]' % (ns_name, page_title)
            else:
                full_page_title = u'[[%s]]' % (page_title)
            yield [full_tl_title, full_page_title]

        cursor.close()
