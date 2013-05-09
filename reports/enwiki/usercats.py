# Copyright 2008, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for user categories
"""

import re

import reports

class report(reports.report):
    def rows_per_page(self):
        return 2250

    def get_title(self):
        return 'User categories'

    def get_preamble_template(self):
        return u'Categories that contain "(wikipedian|\\buser)", "wikiproject" and "participants", or "wikiproject" and "members"; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Category']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* usercats.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8)
        FROM page
        WHERE page_namespace = 14;
        ''')

        for (page_title, ) in cursor:
            if re.search(r'(wikipedian|\buser)', page_title, re.I|re.U) or (re.search(r'(wikiproject)', page_title, re.I|re.U) and re.search(r'(participant|members)', page_title, re.I|re.U)):
                yield [u'[[:Category:%s|]]' % page_title]

        cursor.close()
