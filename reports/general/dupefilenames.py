# Public domain; MZMcBride, Tim Landscheidt; 2011, 2013

"""
Report class for largely duplicative file names
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Largely duplicative file names'

    def get_preamble_template(self):
        return '''Largely duplicative file names (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Normalized name', 'Count', 'Real names']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        /* dupefilenames.py SLOW_OK */
        SELECT
          LOWER(CONVERT(page_title USING utf8)),
          GROUP_CONCAT(CONVERT(page_title USING utf8) SEPARATOR '|'),
          COUNT(*)
        FROM page
        WHERE page_namespace = 6
        AND page_is_redirect = 0
        GROUP BY 1
        HAVING COUNT(*) > 1
        LIMIT 1000;
        ''')
        for norm_name, orig_names_str, count in cursor:
            orig_names = []
            for name in orig_names_str.split('|'):
                name = u'[[:File:%s|%s]]' % (name, name)
                orig_names.append(name)
            orig_name = ', '.join(orig_names)
            yield [norm_name, str(count), orig_name]

        cursor.close()
