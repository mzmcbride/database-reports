# Copyright 2008, 2013 bjweeks, CBM, MZMcBride, Tim Landscheidt

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
Report class for indefinitely semi-protected redirects
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Indefinitely semi-protected redirects'

    def get_preamble_template(self):
        return 'Redirects that are indefinitely semi-protected from editing; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Redirect', 'Protector', 'Timestamp', 'Reason']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* indefsemiredirects.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          CONVERT(user_name USING utf8),
          log_timestamp,
          CONVERT(log_comment USING utf8)
        FROM page_restrictions
        JOIN page
        ON page_id = pr_page
        JOIN logging_userindex
        ON page_namespace = log_namespace
        AND page_title = log_title
        AND log_type = 'protect'
        JOIN user
        ON log_user = user_id
        WHERE page_namespace = 0
        AND pr_type = 'edit'
        AND pr_level = 'autoconfirmed'
        AND pr_expiry = 'infinity'
        AND page_is_redirect = 1
        ORDER BY 1, 3 DESC;
        ''')

        last_page_title = None
        for page_title, user_name, log_timestamp, log_comment in cursor:
            if page_title == last_page_title:
                continue
            last_page_title = page_title
            yield [u'{{plthnr|1=%s}}' % page_title, u'[[User talk:%s|]]' % user_name, log_timestamp, u'<nowiki>%s</nowiki>' % log_comment]

        cursor.close()
