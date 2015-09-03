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
Report class for pages with most revisions
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Page with most revisions'

    def get_preamble_template(self):
        return 'Pages with the most revisions (limited to the first 1000 entries). Data as of %s'

    def get_table_columns(self):
        return ['Namespace ID', 'Page', 'Revisions']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
            /* mostrevisions.py SLOW_OK */
            SELECT
              page_namespace,
              page_title,
              COUNT(*) AS totalrevisions
            FROM revision
            JOIN page
            ON page_id = rev_page
            GROUP BY page_namespace, page_title
            ORDER BY COUNT(*) DESC, page_title ASC
            LIMIT 1000;
        ''')

        for page_namespace, page_title, totalrevisions in cursor:
            page_title = u'{{plh|1={{subst:ns:%s}}:%s}}' % (page_namespace, page_title)
            yield [page_namespace, page_title, totalrevisions]

        cursor.close()
