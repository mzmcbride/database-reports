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
Report class for self-categorized categories
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Self-categorized categories'

    def get_preamble_template(self):
        return 'Self-categorized categories; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Category', 'Members', 'Subcategories']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* selfcatcats.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          cat_pages,
          cat_subcats
        FROM page
        JOIN categorylinks
        ON cl_to = page_title
        RIGHT JOIN category
        ON cat_title = page_title
        WHERE page_id = cl_from
        AND page_namespace = 14;
        ''')

        for page_title, cat_pages, cat_subcats in cursor:
            page_title = u'[[:Category:%s|]]' % page_title
            if not cat_pages:
                cat_pages = ''
            if not cat_subcats:
                cat_subcats = ''
            yield [page_title, str(cat_pages), str(cat_subcats)]

        cursor.close()
