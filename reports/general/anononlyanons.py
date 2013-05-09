# Public domain; bjweeks, MZMcBride, Tim Landscheidt; 2012, 2013

"""
Report class for short user talk pages for IPs
"""

import re

import reports

class report(reports.report):
    def get_title(self):
        return 'Short user talk pages for IPs'

    def get_preamble_template(self):
        return u'''User talk pages of anonymous users where the only contributors to the page \
        are anonymous, the page is less than 50 bytes in length, and it contains no \
        templates (limited to the first 1000 entries); data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Page', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* anononlyanons.py SLOW_OK */
        SELECT CONVERT(ns_name USING utf8), CONVERT(page_title USING utf8), page_len
        FROM page
        JOIN toolserver.namespace ON page_namespace = ns_id
        WHERE page_namespace = 3
          AND page_len < 50
          AND page_title RLIKE '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
          AND NOT EXISTS
            (SELECT TRUE
             FROM revision
             WHERE rev_page = page_id
               AND rev_user != 0)
          AND NOT EXISTS
            (SELECT TRUE
             FROM templatelinks
             WHERE tl_from = page_id)
          AND dbname = CONCAT(?, '_p');
        ''', (self.site, ))

        for ns_name, page_title, page_len in cursor:
            full_page_title = u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)
            yield [full_page_title, str(page_len)]

        cursor.close()
