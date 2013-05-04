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
Report class for uncategorized and unreferenced biographies of living people
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Uncategorized and unreferenced biographies of living people'

    def get_preamble_template(self):
        return u'Pages in [[:Category:All unreferenced BLPs]] in need of proper categorization; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Biography']

    def get_table_rows(self, conn):
        excluded_categories_living = [u'Living_people', u'[0-9]+_births']
        excluded_categories_living_re = u'^(%s)$' % '|'.join(excluded_categories_living)

        cursor = conn.cursor()
        cursor.execute('''
        /* uncatunrefblps.py SLOW_OK */
        SELECT
          DISTINCT CONVERT(page_title USING utf8)
        FROM page
        JOIN categorylinks AS cl1
        ON cl1.cl_from = page_id
        LEFT JOIN categorylinks AS cl2
        ON cl2.cl_from = page_id
        AND cl2.cl_to NOT REGEXP ?
        AND cl2.cl_to NOT IN (SELECT page_title
                              FROM page
                              JOIN categorylinks
                              ON cl_from = page_id
                              WHERE page_namespace = 14
                              AND cl_to IN ('Wikipedia_maintenance', 'Hidden_categories'))
        WHERE cl1.cl_to = 'All_unreferenced_BLPs'
        AND page_namespace = 0
        AND cl2.cl_from IS NULL;
        ''', (excluded_categories_living_re, ))

        for (page_title, ) in cursor:
            yield [u'[[%s]]' % page_title]

        cursor.close()
