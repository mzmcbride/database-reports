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
Report class for templates containing links to disambiguation pages
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Templates containing links to disambiguation pages'

    def get_preamble_template(self):
        return u'''Templates containing links to disambiguation pages (limited results); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Template', 'Disambiguation page', 'Transclusions']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* templatedisambigs.py SLOW_OK */
        SELECT
          CONVERT(pltmp.page_title USING utf8) AS template_title,
          CONVERT(pltmp.pl_title USING utf8) AS disambiguation_title,
          (SELECT COUNT(*) FROM templatelinks WHERE tl_namespace = 10 AND tl_title = pltmp.page_title) AS transclusions_count
        FROM (SELECT
                page_namespace,
                page_title,
                pl_namespace,
                pl_title
              FROM page
              JOIN pagelinks
              ON pl_from = page_id
              WHERE page_namespace = 10
              AND pl_namespace = 0
              LIMIT 1000000) AS pltmp
        JOIN page AS pg2 /* removes red links */
        ON pltmp.pl_namespace = pg2.page_namespace
        AND pltmp.pl_title = pg2.page_title
        WHERE EXISTS (SELECT
                        1
                      FROM categorylinks
                      WHERE pg2.page_id = cl_from
                      AND cl_to = 'All_disambiguation_pages')
        ORDER BY transclusions_count DESC;
        ''')

        for template_title, disambiguation_title, transclusions_count in cursor:
            yield [u'[[Template:%s|%s]]' % (template_title, template_title), u'[[%s]]' % disambiguation_title, str(transclusions_count)]

        cursor.close()
