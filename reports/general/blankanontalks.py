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
Report class for blank user talk pages for IPs
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Blank user talk pages for IPs'

    def get_preamble_template(self):
        return '''Blank user talk pages of anonymous users (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Page']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
/* blankanontalks.py SLOW_OK */
SELECT
  CONVERT(ns_name USING utf8) AS ns_name,
  page_title
FROM page
JOIN toolserver.namespace
ON ns_id = page_namespace
WHERE dbname = ?
AND page_namespace = 3
AND page_title RLIKE ?
AND page_len = 0
LIMIT 1000;
''' , (self.site + '_p', r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'))

        for ns_name, page_title in cursor:
            full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
            yield (full_page_title, )

        cursor.close()
