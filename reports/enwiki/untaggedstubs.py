# Public domain; Topbanana, Legoktm, MZMcBride, Tim Landscheidt; 2012, 2013

"""
Report class for untagged stubs
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Untagged stubs'

    def get_preamble_template(self):
        return u'''Untagged stubs (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Title', 'Length']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* untaggedstubs.py SLOW_OK */
        SELECT
          CONVERT(page_title USING utf8),
          page_len
        FROM page
        LEFT JOIN categorylinks
        ON cl_from = page_id
        AND (cl_to LIKE '%_stubs'
             OR cl_to IN ('All_disambiguation_pages',
                          'All_set_index_articles',
                          'Redirects_to_Wiktionary',
                          'Wikipedia_soft_redirects'))
        WHERE page_namespace = 0
        AND page_is_redirect = 0
        AND page_title NOT LIKE 'List\\_of\\_%'
        AND cl_from IS NULL
        AND page_len < 1500
        LIMIT 1000;
        ''')
        for page_title, page_len in cursor:
            yield ['[[%s]]' % page_title, str(page_len)]

        cursor.close()
