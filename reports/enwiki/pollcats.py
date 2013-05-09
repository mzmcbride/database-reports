# Public domain; bjweeks, MZMcBride, CBM, Tim Landscheidt; 2012, 2013

"""
Report class for polluted categories
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Polluted categories'

    def get_preamble_template(self):
        return u'''Categories that contain pages in the (Main) namespace and the user namespaces \
(limited to the first 1000 entries); data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Category']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* pollcats.py SLOW_OK */
        SELECT
          CONVERT(p1.page_title USING utf8)
        FROM page AS p1
        WHERE p1.page_namespace = 14
        AND NOT EXISTS(SELECT 1
                       FROM templatelinks
                       WHERE tl_from = p1.page_id
                       AND tl_namespace = 10
                       AND tl_title = 'Polluted_category')
        AND EXISTS(SELECT 1
                   FROM page AS p2
                   JOIN categorylinks
                   ON cl_from = p2.page_id
                   WHERE cl_to = p1.page_title
                   AND p2.page_namespace IN (2, 3))
        AND EXISTS(SELECT 1
                   FROM page AS p3
                   JOIN categorylinks
                   ON cl_from = p3.page_id
                   WHERE cl_to = p1.page_title
                   AND p3.page_namespace = 0)
        LIMIT 1000;
        ''')
        for (page_title, ) in cursor:
            yield [u'{{dbr link|1=%s}}' % page_title]

        cursor.close()
