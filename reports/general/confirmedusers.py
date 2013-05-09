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
Report class for autoconfirmed users in the confirmed user group
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Autoconfirmed users in the confirmed user group'

    def get_preamble_template(self):
        return '''Users in the "confirmed" user group who have passed the autoconfirmed threshold; \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['User', 'Edit count', 'First edit']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* confirmedusers.py SLOW_OK */
        SELECT
          CONVERT(user_name USING utf8),
          user_editcount,
          rev_timestamp
        FROM user
        JOIN user_groups
        ON ug_user = user_id
        JOIN revision
        ON rev_user = user_id
        AND ug_group = 'confirmed'
        AND user_editcount > 9
        AND (SELECT
               MIN(rev_timestamp)
             FROM revision
             WHERE rev_user = user_id) < DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 4 DAY),'%Y%m%d%H%i%s')
        AND rev_timestamp = (SELECT
                               MIN(rev_timestamp)
                             FROM revision
                             WHERE rev_user = user_id);
        ''')

        for user_name, user_editcount, rev_timestamp in cursor:
            user_name = u'{{dbr link|1=%s}}' % user_name
            yield [user_name, str(user_editcount), rev_timestamp]

        cursor.close()
