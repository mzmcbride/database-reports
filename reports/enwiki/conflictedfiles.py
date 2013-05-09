# Copyright 2010, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for files with conflicting categorization
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Files with conflicting categorization'

    def get_preamble_template(self):
        return u'''Files that are categorized in [[:Category:All non-free media]] and \
[[:Category:All free media]]; data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['File']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* conflictedfiles.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        JOIN categorylinks AS c1
        ON c1.cl_from = page_id
        JOIN categorylinks AS c2
        ON c2.cl_from = page_id
        WHERE page_namespace = 6
        AND c1.cl_to = 'All_free_media'
        AND c2.cl_to = 'All_non-free_media';
        ''' , (self.site, ))

        for ns_name, page_title in cursor:
            full_page_title = u'[[:%s:%s|%s]]' % (ns_name, page_title, page_title)
            yield [full_page_title]

        cursor.close()
