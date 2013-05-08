# Copyright 2008, 2013 bjweeks, Multichil, MZMcBride, Tim Landscheidt

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
Report class for articles containing red-linked files
"""

import reports

class report(reports.report):
    def needs_commons_db(self):
        return True

    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Articles containing red-linked files'

    def get_preamble_template(self):
        return 'Articles containing a red-linked file; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Article', 'File']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* redlinkedfilesinarticles.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          CONVERT(il_to USING utf8)
        FROM page
        JOIN imagelinks
        ON page_id = il_from
        WHERE NOT EXISTS(SELECT
                           1
                         FROM image
                         WHERE img_name = il_to)
        AND NOT EXISTS(SELECT
                         1
                       FROM commonswiki_f_p.page
                       WHERE page_title = il_to
                       AND page_namespace = 6)
        AND NOT EXISTS(SELECT
                         1
                       FROM page
                       WHERE page_title = il_to
                       AND page_namespace = 6)
        AND page_namespace = 0;
        ''')

        for page_title, il_to in cursor:
            yield [u'[[%s|]]' % page_title, u'[[:File:%s]]' % il_to]

        cursor.close()
