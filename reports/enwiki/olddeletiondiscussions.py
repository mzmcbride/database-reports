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
Report class for old deletion discussions
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Old deletion discussions'

    def get_preamble_template(self):
        return u'Old deletion discussions; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Page', 'Timestamp', 'Category']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* olddeletiondiscussions.py SLOW_OK */
        SELECT
          page_namespace,
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          cl_timestamp,
          CONVERT(cl_to USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        JOIN categorylinks
        ON cl_from = page_id
        WHERE cl_to IN ('Articles_for_deletion',
                        'Templates_for_deletion',
                        'Wikipedia_files_for_deletion',
                        'Categories_for_deletion',
                        'Categories_for_merging',
                        'Categories_for_renaming',
                        'Redirects_for_discussion',
                        'Miscellaneous_pages_for_deletion',
                        'Stub_categories_for_deletion',
                        'Stub_template_deletion_candidates')
        AND cl_timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY)
        AND NOT(page_namespace <> 0 AND cl_to = 'Articles_for_deletion')
        ORDER BY ns_name, page_title ASC;
        ''', (self.site, ))

        for page_namespace, ns_name, page_title, cl_timestamp, cl_to in cursor:
            if page_namespace in (6,14):
                full_page_title = u'[[:%s:%s]]' % (ns_name, page_title)
            elif page_namespace == 0:
                full_page_title = u'[[%s]]' % page_title
            else:
                full_page_title = u'[[%s:%s]]' % (ns_name, page_title)
            full_cl_to = u'[[:Category:%s|%s]]' % (cl_to, cl_to)
            yield [full_page_title, cl_timestamp.strftime('%Y-%m-%d %H:%M:%S'), full_cl_to]

        cursor.close()
