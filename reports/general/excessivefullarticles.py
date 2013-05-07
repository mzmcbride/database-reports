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
Report class for fully protected articles with unusually long expiries
"""

import datetime

import wikitools

import reports

class report(reports.report):
    def get_title(self):
        return 'Fully protected articles with unusually long expiries'

    def get_preamble_template(self):
        return 'Articles that are fully protected from editing for more than one year; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Article', 'Protector', 'Timestamp', 'Expiry', 'Reason']

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
            timestamp = datetime.datetime.strptime(lastlog[0]['timestamp'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M%S')
            user = lastlog[0]['user']
            comment = lastlog[0]['comment']
            return { 'timestamp': timestamp, 'user': user, 'comment': comment }

        cursor = conn.cursor()
        cursor.execute('''
        /* excessivefullarticles.py SLOW_OK */
        SELECT
          page_is_redirect,
          CONVERT(page_title USING utf8),
          pr_expiry
        FROM page_restrictions
        JOIN page
        ON page_id = pr_page
        WHERE page_namespace = 0
        AND pr_type = 'edit'
        AND pr_level = 'sysop'
        AND pr_expiry > DATE_FORMAT(DATE_ADD(NOW(),INTERVAL 1 YEAR),'%Y%m%d%H%i%s')
        AND pr_expiry != 'infinity';
        ''')

        for redirect, page_title, pr_expiry in cursor:
            log_props = last_log_entry(page_title)
            if redirect == 1:
                page_title = u'<i>[[%s]]</i>' % page_title
            else:
                page_title = u'[[%s]]' % page_title
            user = u'[[User talk:%s|]]' % log_props['user']
            timestamp = log_props['timestamp']
            comment = u'<nowiki>%s</nowiki>' % log_props['comment']
            yield [page_title, user, timestamp, str(pr_expiry), comment]

        cursor.close()
