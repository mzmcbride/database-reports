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
Report class for blocked users in user groups
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Blocked users in user groups'

    def get_preamble_template(self):
        return '''Users in user groups who are currently blocked; data as of \
<onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['User', 'User groups', 'Blocker', 'Expiry', 'Reason']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* blockeduserrights.py SLOW_OK */
        SELECT
          CONVERT(user_name USING utf8),
          CONVERT(ug_group USING utf8),
          CONVERT(ipb_by_text USING utf8),
          CONVERT(ipb_expiry USING utf8),
          CONVERT(ipb_reason USING utf8)
        FROM user
        JOIN ipblocks
        ON user_id = ipb_user
        JOIN user_groups
        ON user_id = ug_user;
        ''')

        for user_name, user_groups, ipb_by_text, ipb_expiry, ipb_reason in cursor:
            user_name = u'[[User:%s|]]' % user_name
            ipb_by_text = u'[[User talk:%s|]]' % ipb_by_text
            ipb_reason = u'<nowiki>%s</nowiki>' % ipb_reason
            yield [user_name, user_groups, ipb_by_text, ipb_expiry, ipb_reason]

        cursor.close()
