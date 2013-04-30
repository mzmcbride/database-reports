# Copyright 2009, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for orphaned talk subpages
"""

import datetime

import reports

class report(reports.report):
    def get_title(self):
        return 'Orphaned talk subpages'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return u'Talk pages that don\'t have a root page and do not have a corresponding subject-space page; data as of <onlyinclude>%s</onlyinclude>.' % current_of

    def get_table_columns(self):
        return ['Page']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* orphanedsubtalks.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(pg1.page_title USING utf8)
        FROM page AS pg1
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        WHERE pg1.page_title LIKE '%/%'
        AND pg1.page_namespace IN (1,5,7,9,11,13,101,103)
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS pg2
                        WHERE pg2.page_namespace = pg1.page_namespace
                        AND pg2.page_title = SUBSTRING_INDEX(pg1.page_title, '/', 1))
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS pg3
                        WHERE pg3.page_namespace = pg1.page_namespace - 1
                        AND pg3.page_title = pg1.page_title)
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS pg4
                        WHERE pg4.page_namespace = pg1.page_namespace - 1
                        AND pg4.page_title = SUBSTRING_INDEX(pg1.page_title, '/', 1))
        AND NOT EXISTS (SELECT
                          1
                        FROM templatelinks
                        WHERE tl_from = pg1.page_id
                        AND tl_namespace = 10
                        AND tl_title = 'G8-exempt')
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS pg5
                        WHERE pg5.page_namespace = pg1.page_namespace
                        AND pg5.page_title = LEFT(pg1.page_title, LENGTH(pg1.page_title) - INSTR(REVERSE(pg1.page_title), '/')));
        ''', (self.site, ))

        for ns_name, page_title in cursor:
            yield [u'[[%s:%s]]' % (ns_name, page_title)]

        cursor.close()
