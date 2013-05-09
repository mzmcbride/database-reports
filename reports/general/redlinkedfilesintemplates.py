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
Report class for templates containing red-linked files
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Templates containing red-linked files'

    def get_preamble_template(self):
        return 'Templates containing a red-linked file; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Template', 'File', 'Transclusions', 'File uses']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* redlinkedfilesintemplates.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          CONVERT(il_to USING utf8) AS image_link,
          (SELECT
             COUNT(*)
           FROM templatelinks
           WHERE tl_title = page_title
           AND tl_namespace = 10) AS transclusion_count,
          (SELECT
             COUNT(*)
           FROM imagelinks
           JOIN page AS p2
           ON p2.page_id = il_from
           WHERE image_link = il_to) AS image_count
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        JOIN imagelinks
        ON page_id = il_from
        WHERE (NOT EXISTS (SELECT
                             1
                           FROM image
                           WHERE img_name = il_to))
        AND (NOT EXISTS (SELECT
                           1
                         FROM commonswiki_p.page
                         WHERE page_title = CAST(il_to AS CHAR)
                         AND page_namespace = 6))
        AND (NOT EXISTS (SELECT
                           1
                         FROM page
                         WHERE page_title = il_to
                         AND page_namespace = 6))
        AND page_namespace = 10;
        ''', (self.site, ))

        for ns_name, page_title, image_link, transclusion_count, image_count in cursor:
            page_title = u'{{dbr link|1=%s:%s}}' % (ns_name, page_title)
            il_to = u'{{dbr link|1=:File:%s}}' % image_link
            yield [page_title, il_to, str(transclusion_count), str(image_count)]

        cursor.close()
