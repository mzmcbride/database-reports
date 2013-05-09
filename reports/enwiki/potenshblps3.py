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
Report class for potential biographies of living people (3)
"""

import re

import reports

class report(reports.report):
    def get_title(self):
        return 'Potential biographies of living people (3)'

    def get_preamble_template(self):
        return u'''Articles whose talk pages transclude {{tl|BLP}} that are likely to be biographies \
of living people, but are not in [[:Category:Living people]], [[:Category:Possibly \
living people]], or [[:Category:Missing people]] (limited to the first 1000 \
entries); data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Biography']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* potenshblps3.py SLOW_OK */
        SELECT
          CONVERT(pg1.page_title USING utf8)
        FROM page AS pg1
        JOIN templatelinks
        ON pg1.page_id = tl_from
        WHERE tl_namespace = 10
        AND tl_title = 'BLP'
        AND pg1.page_namespace = 1
        AND NOT EXISTS(SELECT
                         1
                       FROM page AS pg2
                       JOIN categorylinks
                       ON pg2.page_id = cl_from
                       WHERE pg1.page_title = pg2.page_title
                       AND pg2.page_namespace = 0
                       AND (cl_to IN ('Living_people', 'Possibly_living_people', 'Human_name_disambiguation_pages', 'Missing_people')
                            OR cl_to LIKE 'Musical_groups%'
                            OR cl_to LIKE '%music_groups'))
        AND NOT EXISTS(SELECT
                         1
                       FROM page AS pg6
                       JOIN categorylinks
                       ON pg6.page_id = cl_from
                       WHERE pg1.page_title = pg6.page_title
                       AND pg6.page_namespace = 1
                       AND cl_to = 'Musicians_work_group_articles')
        AND NOT EXISTS(SELECT
                         1
                       FROM page AS pg7
                       WHERE pg1.page_title = pg7.page_title
                       AND pg7.page_namespace = 0
                       AND pg7.page_is_redirect = 1)
        AND EXISTS(SELECT
                     1
                   FROM page AS pg8
                   JOIN templatelinks
                   ON pg8.page_id = tl_from
                   WHERE tl_namespace = 10
                   AND tl_title = 'WPBiography'
                   AND pg1.page_title = pg8.page_title
                   AND pg8.page_namespace = 1)
        LIMIT 2000;
        ''')

        i = 1
        for (page_title, ) in cursor:
            page_title = re.sub('_', ' ', page_title)
            if not re.search(r'(^List of|^Line of|\bcontroversy\b|\belection\b|\bmurder(s)?\b|\binvestigation\b|\bkidnapping\b|\baffair\b|\ballegation\b|\brape(s)?\b| v. |\bfamily\b| and |\belection\b|\bband\b| of |\barchive\b|recordholders| & |^The|^[0-9]|\bfiction\b|\bcharacter\b| the |\bincident(s)?\b|\bprinciples\b|\bmost\b)', page_title, re.I) and re.search(r' ', page_title):
                yield ['[[%s]]' % page_title]
                i += 1
                if i > 1000:
                    break

        cursor.close()
