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
Report class for users by bytes uploaded
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Users by bytes uploaded'

    def get_preamble_template(self):
        return u'''Users by bytes uploaded (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

Note this only includes current local file uploads.'''

    def get_table_columns(self):
        return ['User', 'Bytes']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* usersbyupload.py SLOW_OK */
        SELECT
          CONVERT(img_user_text USING utf8),
          SUM(img_size)
        FROM image
        GROUP BY img_user_text
        ORDER BY SUM(img_size) DESC
        LIMIT 1000;
        ''')

        for img_user_text, bytes in cursor:
            yield [img_user_text, str(bytes)]

        cursor.close()
