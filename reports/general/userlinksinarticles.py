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
Report class for articles containing links to the user space
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Articles containing links to the user space'

    def get_preamble_template(self):
        return u'''Articles containing links to the user space; \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Article']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* userlinksinarticles.py SLOW_OK */
        SELECT DISTINCT
          CONVERT(page_title USING utf8)
        FROM page
        JOIN pagelinks
        ON pl_from = page_id
        LEFT JOIN templatelinks
        ON tl_from = page_id
        AND (tl_namespace = 2 AND tl_title = 'Taxobot/children/template' OR
             tl_namespace = 10 AND tl_title IN ('Db-meta', 'Under_construction'))
        WHERE page_namespace = 0
        AND pl_namespace IN (2, 3)
        AND tl_from IS NULL
        ORDER BY 1;
        ''')
        for (page_title, ) in cursor:
            yield ['[[%s]]' % page_title]

        cursor.close()
