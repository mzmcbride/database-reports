# Copyright 2008, 2013 bjweeks, MZMcBride, Tim Landscheidt

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
Report class for mistagged non-free files
"""

import reports

class report(reports.report):
    def needs_commons_db(self):
        return True

    def get_title(self):
        return 'Mistagged non-free files'

    def get_preamble_template(self):
        return 'Mistagged non-free files; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Local file', 'Commons file']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* mistaggedfiles.py SLOW_OK */
        SELECT DISTINCT
          CONVERT(page_title USING utf8),
          CONVERT(repoimg.img_name USING utf8)
        FROM image AS localimg, commonswiki_p.image AS repoimg, categorylinks, page
        WHERE localimg.img_sha1 = repoimg.img_sha1
        AND page_title = localimg.img_name
        AND cl_from = page_id
        AND cl_to = 'All_non-free_media'
        AND localimg.img_sha1 <> 'phoiac9h4m842xq45sp7s6u21eteeq1';
        ''')

        for page_title, img_name in cursor:
            yield [u'[[:File:%s|%s]]' % (page_title, page_title),
                   u'[[:commons:File:%s|%s]]' % (img_name, img_name)]

        cursor.close()
