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
Report class for indefinitely fully protected talk pages
"""

import datetime

import wikitools

import reports

class report(reports.report):
    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Indefinitely fully protected talk pages'

    def get_preamble_template(self):
        return 'Talk pages that are indefinitely fully protected from editing (subpages and redirects excluded); data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Page', 'Protector', 'Timestamp', 'Reason']

    def get_table_rows(self, conn):
        def last_log_entry(page):
            params = {
                'action': 'query',
                'list': 'logevents',
                'lelimit': '1',
                'letitle': page,
                'format': 'json',
                'ledir': 'older',
                'letype': 'protect',
                'leprop': 'user|timestamp|comment'
            }
            request = wikitools.APIRequest(self.wiki, params)
            response = request.query(querycontinue=False)
            lastlog = response['query']['logevents']
            try:
                timestamp = datetime.datetime.strptime(lastlog[0]['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M%S')
            except:
                timestamp = ''
            try:
                user = lastlog[0]['user']
            except:
                user = ''
            try:
                comment = lastlog[0]['comment']
            except:
                comment = ''
            return { 'timestamp': timestamp, 'user': user, 'comment': comment }

        cursor = conn.cursor()
        cursor.execute('''
        /* indeffulltalks.py SLOW_OK */
        SELECT
          page_is_redirect,
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON ns_id = page_namespace
        AND dbname = CONCAT(?, '_p')
        JOIN page_restrictions
        ON page_id = pr_page
        AND page_namespace mod 2 != 0
        AND pr_type = 'edit'
        AND pr_level = 'sysop'
        AND pr_expiry = 'infinity'
        AND page_title NOT LIKE '%/%'
        AND page_is_redirect = 0;
        ''', (self.site, ))

        for redirect, namespace, title in cursor:
            page = wikitools.Page(self.wiki, u'%s:%s' % (namespace, title), followRedir=False)
            page_title = '%s:%s' % (namespace, title)
            page_title = u'{{plh|1=%s}}' % page_title
            log_props = last_log_entry(page.title)
            user = u'[[User talk:%s|]]' % log_props['user']
            timestamp = log_props['timestamp']
            comment = u'<nowiki>%s</nowiki>' % log_props['comment']
            yield [page_title, user, timestamp, comment]

        cursor.close()
