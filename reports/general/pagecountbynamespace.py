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
Report class for page counts by namespace
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Page count by namespace'

    def get_preamble_template(self):
        return 'The number of pages in each [[Wikipedia:Namespace | namespace]]'

    def get_table_columns(self):
        return ['ID', 'Name', 'Non-redirects', 'Redirects', 'Total']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
            SELECT page_namespace, COUNT(*) AS total, SUM(page_is_redirect) AS redirect
            FROM page
            GROUP BY page_namespace
        ''')

        for page_namespace, redirect, total in cursor:
            namespace_name = '{{subst:ns:%s}}' % (page_namespace)
            yield [page_namespace, namespace_name, int(total) - int(redirect), redirect, total]

        cursor.close()
