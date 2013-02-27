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
Report class for indefinitely protected templates without many transclusions
"""

import datetime

import wikitools

import reports

class report(reports.report):
    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Indefinitely protected templates without many transclusions'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
        rep_lag = cursor.fetchone()[0]
        current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

        return '''Indefinitely protected templates without many transclusions (under 100); \
data as of <onlyinclude>%s</onlyinclude>.''' % current_of

    def get_table_columns(self):
        return ['Template', 'Transclusions', 'Admin', 'Timestamp', 'Comment']

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
        /* protlowtemps.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8),
          COUNT(*)
        FROM page
        JOIN templatelinks
        ON tl_namespace = page_namespace
        AND tl_title = page_title
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        JOIN page_restrictions
        ON pr_page = page_id
        WHERE page_namespace = 10
        AND pr_type = 'edit'
        AND pr_level = 'sysop'
        AND pr_expiry = 'infinity'
        GROUP BY page_namespace, page_title
        HAVING COUNT(*) < 100;
        ''', (self.site, ))

        for ns_name, page_title, trans_count in cursor:
            page = wikitools.Page(self.wiki, u'%s:%s' % (ns_name, page_title), followRedir=False)
            page_title = '[[%s]]' % page.title
            try:
                log_props = last_log_entry(page.title)
                user_name = log_props['user']
                log_timestamp = log_props['timestamp']
                log_comment = log_props['comment']
                if log_comment != '':
                    log_comment = u'<nowiki>%s</nowiki>' % log_comment
            except:
                user_name = None
                log_timestamp = None
                log_comment = None
            if user_name is None or log_timestamp is None:
                continue
            yield [page_title, str(trans_count), user_name, log_timestamp, log_comment]

        cursor.close()
