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
Report class for short single-author pages
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Short single-author pages'

    def get_preamble_template(self):
        return 'Templateless non-redirect pages with ten or fewer bytes and a single author; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Page', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* shortpages.py SLOW_OK */
        SELECT
          page_namespace,
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          page_len
        FROM page
        JOIN toolserver.namespace
        ON page_namespace = ns_id
        AND dbname = CONCAT(?, '_p')
        LEFT JOIN templatelinks
        ON tl_from = page_id
        WHERE page_is_redirect = 0
        AND page_namespace NOT IN (8, 10)
        AND (page_namespace NOT IN (2, 3) OR page_title RLIKE '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        AND tl_from IS NULL
        AND page_len < 11
        AND page_len > 0
        AND (SELECT
               COUNT(DISTINCT rev_user_text)
             FROM revision
             WHERE rev_page = page_id) = 1;
        ''', (self.site, ))

        for page_namespace, ns_name, page_title, page_len in cursor:
            if page_namespace in (6, 14):
                page_title = u'{{plh|1=:%s:%s}}' % (ns_name, page_title)
            elif page_namespace == 0:
                page_title = u'{{plh|1=%s}}' % (page_title)
            else:
                page_title = u'{{plh|1=%s:%s}}' % (ns_name, page_title)
            yield [page_title, str(page_len)]

        cursor.close()
