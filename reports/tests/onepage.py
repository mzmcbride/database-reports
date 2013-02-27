"""
Test report class for one page reports.
"""

import datetime

import reports

class report(reports.report):
    def get_title(self):
        return 'Test for one page reports'

    def get_preamble(self, conn):
        return 'Test for one page reports; data as of <onlyinclude>%s</onlyinclude>.' % datetime.datetime.now().strftime('%H:%M, %d %B %Y (UTC)')

    def get_table_columns(self):
        return ['Column 1', 'Column 2', 'Column 3']

    def get_table_rows(self, conn):
        for _ in xrange(500):
            yield ['Some random data', 'Some random data', 'Some random data']
