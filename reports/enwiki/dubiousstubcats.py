# Public domain; MZMcBride, Tim Landscheidt; 2012, 2013

"""
Report class for dubious stub categories
"""

import reports

class report(reports.report):
    def get_title(self):
        return 'Dubious stub categories'

    def get_preamble_template(self):
        return 'Dubious stub categories; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Category']

    def get_table_rows(self, conn):
        cursor = conn.cursor()
        for category in self.get_all_categories_beneath(cursor, 'Stub_categories'):
            if category != 'Stub_categories' and not category.endswith('_stubs'):
                yield [u'[[:Category:%s|%s]]' % (category, category)]

        cursor.close()
