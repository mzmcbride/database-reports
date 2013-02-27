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
Report class for deleted red-linked categories
"""

import datetime

import reports

class report(reports.report):
    def rows_per_page(self):
        return 500

    def get_title(self):
        return 'Deleted red-linked categories'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return 'Deleted red-linked categories; data as of <onlyinclude>%s</onlyinclude>.' % current_of

    def get_table_columns(self):
        return ['Category', 'Members (stored)', 'Members (dynamic)', 'Admin', 'Timestamp', 'Comment']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* deletedredlinkedcats.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(cl_to USING utf8),
          cat_pages,
          log_timestamp,
          CONVERT(user_name USING utf8),
          CONVERT(log_comment USING utf8)
        FROM categorylinks
        JOIN category
        ON cl_to = cat_title
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND ns_id = 14
        LEFT JOIN page
        ON cl_to = page_title
        AND page_namespace = 14
        JOIN logging_ts_alternative
        ON log_type = 'delete'
        AND log_action = 'delete'
        AND log_namespace = 14
        AND log_title = cl_to
        JOIN user
        ON log_user = user_id
        WHERE page_title IS NULL
        AND cat_pages > 0
        ORDER BY cl_to, log_timestamp DESC;
        ''', (self.site, ))

        last_cl_to = None
        for ns_name, cl_to, stored_count, log_timestamp, user_name, log_comment in cursor:
            if cl_to == last_cl_to:
                continue
            last_cl_to = cl_to
            if log_comment:
                log_comment = u'<nowiki>%s</nowiki>' % log_comment
            dynamic_count = u'{{PAGESINCATEGORY:%s}}' % cl_to
            cl_to = u'[[:%s:%s|%s]]' % (ns_name, cl_to, cl_to)
            yield [cl_to, str(stored_count), dynamic_count, user_name, log_timestamp, log_comment]

        cursor.close()
