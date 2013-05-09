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
Report class for articles containing linked e-mail addresses
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Articles containing linked e-mail addresses'

    def get_preamble_template(self):
        return 'Articles containing linked e-mail addresses; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Page']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* linkedemailsinarticles.py SLOW_OK */
        SELECT DISTINCT
          CONVERT(page_title USING utf8)
        FROM externallinks
        JOIN page
        ON el_from = page_id
        WHERE el_to LIKE 'mailto:%'
        AND page_namespace = 0
        LIMIT 1000;
        ''')

        for page_title in cursor:
            yield (u'[[%s]]' % page_title, )

        cursor.close()
