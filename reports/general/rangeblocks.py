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
          CONVERT(ipb_by_text USING utf8),
          ipb_timestamp,
          ipb_expiry,
          CONVERT(ipb_reason USING utf8)
        FROM ipblocks
        WHERE ipb_address LIKE '%/%';
        ''')

        for ipb_address, ipb_by_text, ipb_timestamp, ipb_expiry, ipb_reason in cursor:
            range_size = ipb_address.split('/')[1]
            ipb_address = u'{{ipr|1=%s}}' % ipb_address
            ipb_by_text = u'[[User talk:%s|]]' % ipb_by_text
            if ipb_reason:
                ipb_reason = u'<nowiki>%s</nowiki>' % ipb_reason
            else:
                ipb_reason = ''
            yield [ipb_address, range_size, ipb_by_text, ipb_timestamp, ipb_expiry, ipb_reason]

        cursor.close()
