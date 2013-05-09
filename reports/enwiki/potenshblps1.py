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
Report class for potential biographies of living people (1)
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Potential biographies of living people (1)'

    def get_preamble_template(self):
        return u'''Articles that transclude {{tl|BLP unsourced}} that are not categorized \
in [[:Category:Living people]] or [[:Category:Possibly living people]]; \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Biography']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* potenshblps1.py SLOW_OK */
        SELECT
          CONVERT(pg1.page_title USING utf8)
        FROM page AS pg1
        JOIN templatelinks
        ON pg1.page_id = tl_from
        WHERE pg1.page_namespace = 0
        AND tl_namespace = 10
        AND tl_title = 'BLP_unsourced'
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS pg2
                        JOIN categorylinks
                        ON pg2.page_id = cl_from
                        WHERE pg1.page_title = pg2.page_title
                        AND pg2.page_namespace = 0
                        AND cl_to = 'Living_people')
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS pg3
                        JOIN categorylinks
                        ON pg3.page_id = cl_from
                        WHERE pg1.page_title = pg3.page_title
                        AND pg3.page_namespace = 0
                        AND cl_to = 'Possibly_living_people')
        AND NOT EXISTS (SELECT
                          1
                        FROM page AS pg4
                        JOIN categorylinks
                        ON pg4.page_id = cl_from
                        WHERE pg1.page_title = pg4.page_title
                        AND pg4.page_namespace = 0
                        AND cl_to RLIKE '^[0-9]{4}_deaths$');
        ''')

        for (page_title, ) in cursor:
            yield [u'[[%s]]' % page_title]

        cursor.close()
