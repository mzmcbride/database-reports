# Public domain; bjweeks, MZMcBride, Tim Landscheidt; 2011, 2013

"""
Report class for unused templates
"""

import reports

class report(reports.report):
    def rows_per_page(self):
        return 1000

    def get_title(self):
        return 'Unused templates'

    def get_preamble_template(self):
        return 'Unused templates; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Template']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* unusedtemplates.py SLOW_OK */
        SELECT
          CONVERT(ns_name USING utf8),
          CONVERT(page_title USING utf8)
        FROM page
        JOIN toolserver.namespace
        ON dbname = CONCAT(?, '_p')
        AND page_namespace = ns_id
        LEFT JOIN categorylinks
        ON page_id = cl_from
        AND cl_to = 'Wikipedia_substituted_templates'
        LEFT JOIN redirect
        ON rd_from = page_id
        LEFT JOIN templatelinks
        ON page_namespace = tl_namespace
        AND page_title = tl_title
        WHERE page_namespace = 10
        AND rd_from IS NULL
        AND tl_from IS NULL
        AND cl_from IS NULL;
        ''', (self.site, ))

        for ns_name, page_title in cursor:
            if (not page_title.endswith('/doc') and
                not page_title.endswith('/testcases') and
                not page_title.endswith('/sandbox') and
                not page_title.startswith('Editnotices/') and
                not page_title.startswith('Cite_doi/') and
                not page_title.startswith('Cite_pmid/') and
                not page_title.startswith('TFA_title/') and
                not page_title.startswith('POTD_protected/') and
                not page_title.startswith('POTD_credit/') and
                not page_title.startswith('POTD_caption/') and
                not page_title.startswith('Did_you_know_nominations/') and
                not page_title.startswith('Child_taxa//')):
                yield [u'[[%s:%s|%s]]' % (ns_name, page_title, page_title)]

        cursor.close()
