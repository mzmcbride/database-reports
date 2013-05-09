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
Report class for biographies of living people possibly eligible for deletion
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Biographies of living people possibly eligible for deletion'

    def get_preamble_template(self):
        return u'''Biographies of living people possibly eligible for deletion. Biographies \
in [[:Category:BLP articles proposed for deletion]] or [[:Category:Articles for deletion]] \
are marked in bold. Data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Biography', 'First edit']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* stickyprodblps.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          rev_timestamp,
          EXISTS(SELECT
                   1
                 FROM categorylinks
                 WHERE cl_from = page_id
                 AND cl_to IN ('BLP_articles_proposed_for_deletion', 'Articles for deletion'))
        FROM page
        JOIN revision
        ON rev_page = page_id
        JOIN categorylinks
        ON cl_from = page_id
        WHERE cl_to = 'All_unreferenced_BLPs'
        AND page_namespace = 0
        AND page_is_redirect = 0
        AND rev_timestamp = (SELECT
                               MIN(rev_timestamp)
                             FROM revision AS last
                             WHERE last.rev_page = page_id)
        AND rev_timestamp > '20100318000000';
        ''')

        for page_title, rev_timestamp, is_categorized in cursor:
            if is_categorized:
                page_title = u'<b>{{dbr link|1=%s}}</b>' % page_title
            else:
                page_title = u'{{dbr link|1=%s}}' % page_title
            yield [page_title, rev_timestamp]

        cursor.close()
