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
Report class for potential reviewer candidates
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 2000

    def get_title(self):
        return 'Potential reviewer candidates'

    def get_preamble_template(self):
        return u'''Users with more than 2,500 edits, their first edit more than a year ago, \
and their latest edit within the past month; data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['User', 'Edit count', 'First edit', 'Latest edit', 'Groups']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* reviewercandidates.py SLOW_OK */
        SELECT DISTINCT
          CONVERT(usrtmp.user_name USING utf8),
          usrtmp.user_editcount,
          usrtmp.rev_timestamp AS first_edit,
          rv1.rev_timestamp AS last_edit,
          IFNULL(usrtmp.groups, '')
        FROM revision AS rv1
        JOIN (SELECT
                user_id,
                user_name,
                user_editcount,
                rev_timestamp,
                GROUP_CONCAT(CONVERT(ug_group USING utf8) ORDER BY CONVERT(ug_group USING utf8) SEPARATOR ', ') AS groups
              FROM user
              LEFT JOIN user_groups
              ON ug_user = user_id
              JOIN revision
              ON rev_user = user_id
              WHERE user_editcount > 2500
              AND user_id NOT IN (SELECT
                                    ug_user
                                  FROM user_groups
                                  WHERE ug_group IN ('bot', 'sysop', 'reviewer'))
              AND user_name NOT IN (SELECT DISTINCT
                                      REPLACE(pl_title, '_', ' ')
                                    FROM pagelinks
                                    JOIN page
                                    ON pl_from = page_id
                                    WHERE page_namespace = 4
                                    AND page_title = 'Database_reports/Potential_reviewer_candidates/Exceptions'
                                    AND pl_namespace IN (2, 3)
                                    AND pl_title NOT LIKE '%/%')
              AND rev_timestamp = (SELECT
                                     MIN(rev_timestamp)
                                   FROM revision
                                   WHERE rev_user = user_id)
              AND rev_timestamp < DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 YEAR), '%Y%m%d%H%i%s')
              GROUP BY user_id) AS usrtmp
        ON usrtmp.user_id = rv1.rev_user
        WHERE rv1.rev_timestamp = (SELECT
                                     MAX(rev_timestamp)
                                   FROM revision
                                   WHERE rev_user = usrtmp.user_id)
        AND rv1.rev_timestamp > DATE_FORMAT(DATE_SUB(NOW(), INTERVAL 1 MONTH), '%Y%m%d%H%i%s')
        ORDER BY usrtmp.user_name ASC;
        ''')

        for user_name, user_editcount, first_edit, last_edit, groups in cursor:
            yield [user_name, str(user_editcount), first_edit, last_edit, groups]

        cursor.close()
