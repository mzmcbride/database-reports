# Public domain; MZMcBride, Tim Landscheidt; 2011, 2013

"""
Report class for files with the most uses globally
"""

import datetime

import reports

class report(reports.report):
    def get_title(self):
        return 'Files with the most uses globally'

    def get_preamble(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT
                         UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp)
                       FROM recentchanges
                       ORDER BY rc_timestamp DESC
                       LIMIT 1;
                       ''')
        rep_lag = cursor.fetchone()[0]
        time_diff = datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)
        current_of = time_diff.strftime('%H:%M, %d %B %Y (UTC)')

        return u'Files with the most uses globally; data as of <onlyinclude>%s</onlyinclude>.' % current_of

    def get_table_columns(self):
        return ['File', 'Uses']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* mostglobalfileusage.py SLOW_OK */
        SELECT
          CONVERT(gil_to USING utf8),
          COUNT(*)
        FROM globalimagelinks
        GROUP BY gil_to
        ORDER BY COUNT(*) DESC, gil_to ASC
        LIMIT 1000;
        ''')

        for gil_to, count in cursor:
            yield [u'[[:File:%s|%s]]' % (gil_to, gil_to), str(count)]

        cursor.close()
