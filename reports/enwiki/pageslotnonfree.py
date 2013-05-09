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
Report class for pages containing an unusually high number of non-free files
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Pages containing an unusually high number of non-free files'

    def get_preamble_template(self):
        return u'''Pages containing an unusually high number of non-free files; \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Page', 'Non-free files']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* pageslotnonfree.py SLOW_OK */
        SELECT
          imgtmp.page_namespace,
          CONVERT(imgtmp.ns_name USING utf8),
          CONVERT(imgtmp.page_title USING utf8),
          COUNT(cl_to)
        FROM page AS pg1
        JOIN categorylinks
        ON cl_from = pg1.page_id
        JOIN (SELECT
                pg2.page_namespace,
                ns_name,
                pg2.page_title,
                il_to
              FROM page AS pg2
              JOIN toolserver.namespace
              ON dbname = CONCAT(?, '_p')
              AND pg2.page_namespace = ns_id
              JOIN imagelinks
              ON il_from = page_id) AS imgtmp
        ON il_to = pg1.page_title
        WHERE pg1.page_namespace = 6
        AND cl_to = 'All_non-free_media'
        GROUP BY imgtmp.page_namespace, imgtmp.page_title
        HAVING COUNT(cl_to) > 6
        ORDER BY COUNT(cl_to) DESC;
        ''', (self.site, ))

        for page_namespace, ns_name, page_title, count in cursor:
            if page_namespace == 6 or page_namespace == 14:
                page_title = u'[[:%s:%s]]' % (ns_name, page_title)
            elif page_namespace == 0:
                page_title = u'[[%s]]' % page_title
            else:
                page_title = u'[[%s:%s]]' % (ns_name, page_title)
            yield [page_title, str(count)]

        cursor.close()
