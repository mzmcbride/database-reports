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
Report class for transclusions of deleted templates
"""

import datetime

import reports

class report(reports.report):
    def rows_per_page(self):
        return 1000

    def get_title(self):
        return 'Transclusions of deleted templates'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return 'Transclusions of deleted templates; data as of <onlyinclude>%s</onlyinclude>.' % current_of

    def get_table_columns(self):
        return ['Template', 'Transclusions']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* deletedtrans.py SLOW_OK */
        SELECT
          CONVERT(tl_title USING utf8),
          COUNT(DISTINCT tl_from)
        FROM templatelinks
        LEFT JOIN page AS p1
        ON p1.page_namespace = tl_namespace
        AND p1.page_title = tl_title
        JOIN logging_ts_alternative
        ON tl_namespace = log_namespace
        AND tl_title = log_title
        AND log_type = 'delete'
        JOIN page AS p2
        ON tl_from = p2.page_id
        WHERE p1.page_id IS NULL
        AND tl_namespace = 10
        GROUP BY tl_title
        ORDER BY COUNT(DISTINCT tl_from) DESC
        LIMIT 4000;
        ''')

        for tl_title, count in cursor:
            yield [u'{{dbr link|1=%s}}' % tl_title, str(count)]

        cursor.close()
