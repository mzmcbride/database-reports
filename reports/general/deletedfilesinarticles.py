# Copyright 2010, 2013 bjweeks, Multichil, MZMcBride, Tim Landscheidt

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
Report class for articles containing deleted files
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 1000

    def get_title(self):
        return 'Articles containing deleted files'

    def get_preamble_template(self):
        return u'Articles containing a deleted file; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Article', 'File', 'Timestamp', 'Comment']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* deletedfilesinarticles.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          CONVERT(il_to USING utf8),
          log_timestamp,
          CONVERT(log_comment USING utf8)
        FROM page
        JOIN imagelinks
        ON page_id = il_from
        JOIN logging_ts_alternative
        ON log_type = 'delete'
        AND log_action = 'delete'
        AND log_namespace = 6
        AND log_title = il_to
        WHERE (NOT EXISTS (SELECT
                             1
                           FROM image
                           WHERE img_name = il_to))
        AND (NOT EXISTS (SELECT
                           1
                         FROM commonswiki_p.page
                         WHERE page_title = CAST(il_to AS CHAR)
                         AND page_namespace = 6))
        AND (NOT EXISTS (SELECT
                           1
                         FROM page
                         WHERE page_title = il_to
                         AND page_namespace = 6))
        AND page_namespace = 0
        ORDER BY il_to, log_timestamp DESC
        ''')

        last_il_lo = None
        for page_title, il_to, log_timestamp, log_comment in cursor:
            if il_to == last_il_lo:
                continue
            last_il_lo = il_to
            yield [u'[[%s]]' % page_title, u'[[:File:%s|%s]]' % (il_to, il_to), log_timestamp, '<nowiki>%s</nowiki>' % log_comment]

        cursor.close()
