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
Report class for uncategorized categories
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Uncategorized categories'

    def get_preamble_template(self):
        return 'Uncategorized categories; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Category', 'Length', 'Members', 'Last edit', 'Last user']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* uncatcats.py SLOW_OK */
        SELECT
          page_title,
          page_len,
          cat_pages,
          rev_timestamp,
          CONVERT(rev_user_text USING utf8)
        FROM revision
        JOIN
        (SELECT
           page_id,
           CONVERT(page_title USING utf8) AS page_title,
           page_len,
           cat_pages
         FROM category
         RIGHT JOIN page
         ON cat_title = page_title
         LEFT JOIN categorylinks
         ON page_id = cl_from
         WHERE cl_from IS NULL
         AND page_namespace = 14
         AND page_is_redirect = 0) AS pagetmp
        ON rev_page = pagetmp.page_id
        AND rev_timestamp = (SELECT
                               MAX(rev_timestamp)
                             FROM revision AS last
                             WHERE last.rev_page = pagetmp.page_id);
        ''')

        for page_title, page_len, cat_pages, rev_timestamp, rev_user_text in cursor:
            if page_title:
                page_title = u'{{clh|1=%s}}' % page_title
            if not cat_pages:
                cat_pages = ''
            yield [page_title, str(page_len), str(cat_pages), rev_timestamp, rev_user_text]

        cursor.close()
