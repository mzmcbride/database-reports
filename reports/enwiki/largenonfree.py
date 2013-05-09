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
Report class for large non-free files
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Large non-free files'

    def get_preamble_template(self):
        return u'''Files in [[:Category:All non-free media]] that are larger than 999999 bytes \
and are not in [[:Category:Non-free Wikipedia file size reduction request]]; \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['File', 'Size']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* largenonfree.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          img_size
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        JOIN image
        ON img_name = page_title
        JOIN categorylinks
        ON cl_from = page_id
        WHERE page_namespace = 6
        AND cl_to = 'All_non-free_media'
        AND img_size > 999999
        AND NOT EXISTS (SELECT
                          1
                        FROM categorylinks
                        WHERE page_id = cl_from
                        AND cl_to = 'Non-free_Wikipedia_file_size_reduction_request');
        ''', (self.site, ))

        for ns_name, page_title, img_size in cursor:
            yield [u'[[:%s:%s|%s]]' % (ns_name, page_title, page_title), str(img_size)]

        cursor.close()
