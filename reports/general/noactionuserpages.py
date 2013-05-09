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
Report class for user pages for inactive IPs
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'User pages for inactive IPs'

    def get_preamble_template(self):
        return u'''User pages of anonymous users without any contributions (live or deleted), \
blocks, or abuse filter matches (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Page', 'Length']

    def get_table_rows(self, conn):
        blocks = set()
        abuse_filter_matches = set()

        cursor = conn.cursor()
        cursor.execute('''
        /* noactionuserpages.py SLOW_OK */
        SELECT
          CONVERT(log_title USING utf8)
        FROM logging
        WHERE log_type = 'block'
        AND log_namespace = 2
        AND log_title RLIKE ?;
        ''', (r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ))
        for log_title in cursor:
            blocks.add(log_title)

        cursor.execute('''
        /* noactionuserpages.py SLOW_OK */
        SELECT
          afl_user_text
        FROM abuse_filter_log
        WHERE afl_user_text RLIKE ?;
        ''', (r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ))
        for afl_user_text in cursor:
            abuse_filter_matches.add(afl_user_text)

        cursor.execute('''
        /* noactionuserpages.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          page_len
        FROM page
        LEFT JOIN revision
        ON rev_user_text = page_title
        LEFT JOIN archive
        ON ar_user_text = page_title
        JOIN toolserver.namespace
        ON ns_id = page_namespace
        AND dbname = CONCAT(?, '_p')
        WHERE page_namespace = 2
        AND ISNULL(rev_user_text)
        AND ISNULL(ar_user_text)
        AND page_title RLIKE ?;
        ''', (self.site, r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'))

        i = 1
        for ns_name, page_title, page_len in cursor:
            full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
            if page_title not in blocks and page_title not in abuse_filter_matches:
                yield [full_page_title, str(page_len)]
                i = i + 1
                if i > 1000:
                    break

        cursor.close()
