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
Report class for forgotten articles
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 1000

    def get_title(self):
        return 'Forgotten articles'

    def get_preamble_template(self):
        return 'List of oldest 1000 edited articles. Data as of: %s.'

    def get_table_columns(self):
        return ['Article', 'Timestamp of last edit', 'Number of edits yet']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* forgotten_articles.py */
        SELECT p.page_title, p.page_namespace, p.page_is_redirect, p.page_touched, r.editcount FROM page p
        LEFT JOIN ( 
          SELECT COUNT(*) AS editcount, rev_page FROM revision 
          GROUP BY rev_page 
        ) r ON r.rev_page = p.page_id
        WHERE page_is_redirect = 0 AND page_namespace = 0 
        ORDER BY page_touched 
        LIMIT 1000
        ''')

        for page_title, page_touched, editcount, page_namespace, page_is_redirect in cursor:
            page_title = u'[[%s]]' % page_title
            page_touched = datetime.datetime.strptime( page_touched, '%Y%m%d%H%M%S (UTC)')
            yield [page_title, page_touched, str(editcount)]

        cursor.close()
