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
Report class for file description pages containing no templates or categories
"""

import datetime

import reports

class report(reports.report):
    def needs_commons_db(self):
        return True

    def get_title(self):
        return 'File description pages containing no templates or categories'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return u'''File description pages containing no templates or categories (limited to the \
first 800 entries); data as of <onlyinclude>%s</onlyinclude>.''' % current_of

    def get_table_columns(self):
        return ['Page', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* catandtemplessfilepages.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          page_len
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND ns_id = page_namespace
        LEFT JOIN templatelinks
        ON tl_from = page_id
        LEFT JOIN categorylinks
        ON cl_from = page_id
        WHERE NOT EXISTS (SELECT
                            img_name
                          FROM commonswiki_p.image
                          WHERE img_name = CONVERT(page_title USING utf8))
        AND page_namespace = 6
        AND page_is_redirect = 0
        AND tl_from IS NULL
        AND cl_from IS NULL
        LIMIT 800;
        ''', (self.site, ))

        for ns_name, page_title, page_len in cursor:
            yield [u'[[:%s:%s|]]' % (ns_name, page_title), str(page_len)]

        cursor.close()
