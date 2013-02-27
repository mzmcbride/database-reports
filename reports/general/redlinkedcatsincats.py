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
Report class for categories categorized in red-linked categories
"""

import datetime

import reports

class report(reports.report):
    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Categories categorized in red-linked categories'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return 'Categories categorized in red-linked categories; data as of <onlyinclude>%s</onlyinclude>.' % current_of

    def get_table_columns(self):
        return ['Category', 'Member category']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* redlinkedcatsincats.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          CONVERT(cl_to USING utf8)
        FROM page
        JOIN
        (SELECT
           cl_to,
           cl_from
         FROM categorylinks
         LEFT JOIN page
         ON cl_to = page_title
         AND page_namespace = 14
         WHERE page_title IS NULL) AS cattmp
        ON cattmp.cl_from = page_id
        WHERE page_namespace = 14;
        ''')

        for page_title, cl_to in cursor:
            page_title = u'{{clh|1=%s}}' % page_title
            cl_to = u'[[:Category:%s|]]' % cl_to
            yield [page_title, cl_to]

        cursor.close()
