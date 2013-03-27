# Copyright 2010, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for untagged and unreferenced biographies of living people
"""

import datetime
import re

import reports

class report(reports.report):
    def get_title(self):
        return 'Untagged and unreferenced biographies of living people'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return u'''Pages in [[:Category:All unreferenced BLPs]] missing WikiProject tags; \
data as of <onlyinclude>%s</onlyinclude>.''' % current_of

    def get_table_columns(self):
        return ['Biography', 'Categories']

    def get_table_rows(self, conn):
        excluded_categories_re = re.compile(r'(\d{1,4}_births|living_people|all_unreferenced_blps|unreferenced_blps_from)', re.I)

        cursor = conn.cursor()
        cursor.execute('''
        /* untaggedunrefblps.py SLOW_OK */
        SELECT
          CONVERT(p1.page_title USING utf8),
          GROUP_CONCAT(CONVERT(cl2.cl_to USING utf8) SEPARATOR '|')
        FROM page AS p1
        JOIN categorylinks AS cl1
        ON cl1.cl_from = p1.page_id
        JOIN categorylinks AS cl2
        ON cl2.cl_from = p1.page_id
        WHERE cl1.cl_to = 'All_unreferenced_BLPs'
        AND p1.page_namespace = 0
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS p2
                        WHERE p2.page_title = p1.page_title
                        AND p2.page_namespace = 1)
        GROUP BY p1.page_id;
        ''')

        for page_title, categories in cursor:
            page_title = u'{{plat|1=%s}}' % page_title
            category_col = []
            for category in categories.split('|'):
                if not excluded_categories_re.search(category):
                    category_col.append(u'[[:Category:%s|%s]]' % (category, category))
            category_links = u', '.join(category_col)
            yield [page_title, category_links]

        cursor.close()
