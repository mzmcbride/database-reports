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
Report class for range blocks
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Range blocks'

    def get_preamble_template(self):
        return 'Range blocks; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Range', 'Size', 'Admin', 'Timestamp', 'Expiry', 'Reason']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* rangeblocks.py SLOW_OK */
        SELECT
          ipb_address,
          CONVERT(actor_name USING utf8),
          ipb_timestamp,
          ipb_expiry,
          CONVERT(comment_text USING utf8)
        FROM ipblocks
        INNER JOIN actor
          ON ipb_by_actor = actor_id
        INNER JOIN comment
          ON ipb_reason_id = comment_id
        WHERE ipb_address LIKE '%/%';
        ''')

        for ipb_address, actor_name, ipb_timestamp, ipb_expiry, comment_text in cursor:
            range_size = ipb_address.split('/')[1]
            ipb_address = u'{{ipr|1=%s}}' % ipb_address
            actor_name = u'[[User talk:%s|]]' % actor_name
            if comment_text:
                comment_text = u'<nowiki>%s</nowiki>' % comment_text
            else:
                comment_text = ''
            yield [ipb_address, range_size, actor_name, ipb_timestamp, ipb_expiry, comment_text]

        cursor.close()
