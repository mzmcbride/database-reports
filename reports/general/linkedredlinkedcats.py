# Public domain; MZMcBride, Tim Landscheidt; 2012, 2013

"""
Report class for red-linked categories with incoming links
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Red-linked categories with incoming links'

    def get_preamble_template(self):
        return 'Red-linked categories with incoming links; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Category', 'Links']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* linkedredlinkedcats.py SLOW_OK */
        SELECT
          CONVERT(cl_to USING utf8),
          COUNT(*)
        FROM categorylinks
        JOIN pagelinks ON pl_title = cl_to AND pl_namespace = 14
        JOIN page AS p1 ON pl_from = p1.page_id AND p1.page_namespace IN (0, 6, 10, 12, 14, 100)
        LEFT JOIN page AS p2 ON cl_to = p2.page_title AND p2.page_namespace = 14
        WHERE p2.page_title IS NULL
        GROUP BY 1 LIMIT 1000;
        ''')

        for cl_to, links in cursor:
            category_link = u'[[Special:WhatLinksHere/Category:%s|%s]]' % (cl_to, cl_to)
            yield [category_link, str(links)]

        cursor.close()
