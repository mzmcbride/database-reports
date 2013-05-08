# Public domain; MZMcBride, Tim Landscheidt; 2012, 2013

"""
Report class for stubs included directly in stub categories
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 800

    def get_title(self):
        return 'Stubs included directly in stub categories'

    def get_preamble_template(self):
        return u'Stubs included directly in stub categories; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Article', 'Category']

    def get_table_rows(self, conn):
        # Basically, what we're looking for are articles in
        # category CAT that do not transclude templates in
        # category CAT and do not transclude templates
        # redirecting to templates in category CAT,
        # i. e. the category has been added either directly
        # in wikitext or by another template.
        cursor = conn.cursor()
        for category in self.get_all_categories_beneath(cursor, 'Stub_categories'):
            cursor.execute('''
                           SELECT
                             CONVERT(p1.page_title USING utf8)
                           FROM page AS p1
                           JOIN categorylinks AS c1
                           ON c1.cl_from = p1.page_id
                           WHERE p1.page_namespace = 0
                           AND p1.page_is_redirect = 0
                           AND c1.cl_to = CONVERT(? USING utf8)
                           AND NOT EXISTS(SELECT 1 FROM templatelinks
                                          JOIN page AS p2
                                          ON tl_namespace = p2.page_namespace
                                          AND tl_title = p2.page_title
                                          JOIN categorylinks AS c2
                                          ON p2.page_id = c2.cl_from
                                          AND c2.cl_to = CONVERT(? USING utf8)
                                          WHERE tl_from = p1.page_id
                                          AND tl_title LIKE '%-stub')
                           AND NOT EXISTS(SELECT 1 FROM templatelinks
                                          JOIN page AS p2
                                          ON tl_namespace = p2.page_namespace
                                          AND tl_title = p2.page_title
                                          JOIN redirect
                                          ON p2.page_id = rd_from
                                          JOIN page AS p3
                                          ON rd_namespace = p3.page_namespace
                                          AND rd_title = p3.page_title
                                          JOIN categorylinks AS c2
                                          ON p3.page_id = c2.cl_from
                                          AND c2.cl_to = CONVERT(? USING utf8)
                                          WHERE tl_from = p1.page_id
                                          AND tl_title LIKE '%-stub');
                           ''', (category, category, category))
            for (page_title, ) in cursor:
                yield [u'[[%s]]' % page_title, u'[[:Category:%s|%s]]' % (category, category)]

        cursor.close()
