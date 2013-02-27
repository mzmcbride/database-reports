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
Report class for old IP talk pages
"""

import datetime

import reports

class report(reports.report):
    def get_title(self):
        return 'Old IP talk pages'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return u'''Old IP talk pages where the IP has never been blocked and has not edited in the past year and \
where the IP's talk page has not had any activity in the past year, has no incoming links, \
and contains no unsubstituted templates (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.''' % current_of

    def get_table_columns(self):
        return ['IP', 'Last talk page activity', 'Last IP activity', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* oldiptalks.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          r1.rev_timestamp,
          r2.rev_timestamp,
          page_len
        FROM page
        JOIN revision AS r1
        ON page_title = r1.rev_user_text
        JOIN revision AS r2
        ON page_id = r2.rev_page
        LEFT JOIN pagelinks
        ON page_namespace = pl_namespace
        AND page_title = pl_title
        LEFT JOIN templatelinks
        ON tl_from = page_id
        WHERE page_namespace = 3
        AND pl_namespace IS NULL
        AND tl_from IS NULL
        AND page_title RLIKE '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        AND r1.rev_timestamp = (SELECT
                                  MAX(rev_timestamp)
                                FROM revision
                                WHERE rev_user_text = page_title)
        AND (SELECT
               MAX(rev_timestamp)
             FROM revision
             WHERE rev_user_text = page_title) < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 1 YEAR),'%Y%m%d%H%i%s')
        AND NOT EXISTS (SELECT
                          1
                        FROM logging_ts_alternative
                        WHERE log_namespace = 2
                        AND log_title = page_title
                        AND log_type = 'block')
        AND r2.rev_timestamp = (SELECT
                                  MAX(rev_timestamp)
                                FROM revision
                                WHERE rev_page = page_id)
        AND (SELECT
               MAX(rev_timestamp)
             FROM revision
             WHERE rev_page = page_id) < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 1 YEAR),'%Y%m%d%H%i%s')
        LIMIT 1000;
        ''')

        for page_title, last_talk_page_activity, last_ip_activity, page_len in cursor:
            page_title = u'[[User talk:%s|%s]]' % (page_title, page_title)
            yield [page_title, last_talk_page_activity, last_ip_activity, str(page_len)]

        cursor.close()
