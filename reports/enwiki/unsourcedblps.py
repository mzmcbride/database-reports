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
Report class for biographies of living people containing unsourced statements
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Biographies of living people containing unsourced statements'

    def get_preamble_template(self):
        return u'''{{shortcut|WP:DR/BLP}}
Pages in [[:Category:Living people]] that [[Special:WhatLinksHere/Template:Citation needed|transclude]] \
[[Template:Citation needed]] (limited to the first 500 entries); data as of <onlyinclude>%s</onlyinclude>. \
{{NOINDEX}}'''

    def get_table_columns(self):
        return ['Article']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* unsourcedblps.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8)
        FROM page
        JOIN templatelinks
        ON tl_from = page_id
        JOIN categorylinks
        ON cl_from = page_id
        WHERE cl_to = 'Living_people'
        AND tl_namespace = 10
        AND tl_title = 'Citation_needed'
        AND page_namespace = 0
        LIMIT 500;
        ''')

        for (page_title, ) in cursor:
            yield [u'{{ple|1=%s}}' % page_title]

        cursor.close()
