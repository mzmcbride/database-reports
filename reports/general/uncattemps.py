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
Report class for uncategorized templates
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Uncategorized templates'

    def get_preamble_template(self):
        return u'''Uncategorized templates (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Template']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* uncattemps.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        LEFT JOIN categorylinks
        ON cl_from = page_id
        WHERE page_namespace = 10
        AND page_is_redirect = 0
        AND ISNULL(cl_from)
        AND page_title NOT LIKE '%/%'
        LIMIT 1000;
        ''' , (self.site, ))

        for ns_name, page_title in cursor:
            full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
            yield [full_page_title]

        cursor.close()
