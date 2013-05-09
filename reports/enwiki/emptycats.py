# Copyright 2008, 2013 bjweeks, MZMcBride, CBM, Tim Landscheidt

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
Report class for empty categories
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Empty categories'

    def get_preamble_template(self):
        return u'''Empty categories not in [[:Category:Wikipedia category redirects]], not in \
[[:Category:Disambiguation categories]], and do not contain "(-importance|\
-class|non-article|assess|articles missing|articles in need of|articles undergoing|\
articles to be|articles not yet|articles with|articles without|articles needing|\
Wikipedia featured topics)"; data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Category', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* emptycats.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          page_len
        FROM categorylinks
        RIGHT JOIN page ON cl_to = page_title
        WHERE page_namespace = 14
        AND page_is_redirect = 0
        AND cl_to IS NULL
        AND NOT(CONVERT(page_title USING utf8) REGEXP '(-importance|-class|non-article|assess|_articles_missing_|_articles_in_need_of_|_articles_undergoing_|_articles_to_be_|_articles_not_yet_|_articles_with_|_articles_without_|_articles_needing_|Wikipedia_featured_topics)')
        AND NOT EXISTS (SELECT
                          1
                        FROM categorylinks
                        WHERE cl_from = page_id
                        AND (cl_to = 'Wikipedia_soft_redirected_categories' OR
                             cl_to = 'Disambiguation_categories' OR
                             cl_to LIKE 'Empty_categories%'))
        AND NOT EXISTS (SELECT
                          1
                        FROM templatelinks
                        WHERE tl_from = page_id
                        AND tl_namespace = 10
                        AND tl_title = 'Empty_category');
        ''')

        for page_title, page_len in cursor:
            yield [u'{{clh|1=%s}}' % page_title, str(page_len)]

        cursor.close()
