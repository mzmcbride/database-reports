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
Report class for file description pages without an associated file
"""

import datetime

import reports

class report(reports.report):
    def needs_commons_db(self):
        return True

    def get_title(self):
        return 'File description pages without an associated file'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return 'File description pages without an associated file; data as of <onlyinclude>%s</onlyinclude>.' % current_of

    def get_table_columns(self):
        return ['Page']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* filelessfilepages.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(pg1.page_title USING utf8)
        FROM page AS pg1
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND pg1.page_namespace = ns_id
        WHERE NOT EXISTS (SELECT
                            img_name
                          FROM image
                          WHERE img_name = pg1.page_title)
        AND NOT EXISTS (SELECT
                          img_name
                        FROM commonswiki_p.image
                        WHERE img_name = CAST(pg1.page_title AS CHAR))
        AND NOT EXISTS (SELECT
                          1
                        FROM commonswiki_p.page AS pg2
                        WHERE pg2.page_namespace = 6
                        AND pg2.page_title = CAST(pg1.page_title AS CHAR)
                        AND pg2.page_is_redirect = 1)
        AND pg1.page_namespace = 6
        AND pg1.page_is_redirect = 0;
        ''', (self.site, ))

        for ns_name, page_title in cursor:
            page_title = '[[:%s:%s|]]' % (ns_name, page_title)
            yield [page_title]

        cursor.close()
